from re import finditer
from queue import Queue, Empty
from threading import Thread, Event
from time import gmtime, strftime
from unicodedata import east_asian_width as width
from wikitools import wiki
from wikitools.page import Page

pairs = [
  ['\\(', '\\)'],
  ['（', '）'],
  ['\\[', '\\]'],
  ['{', '}'],
  ['<!--', '-->'],
  ['<([a-zA-Z]*)(?: [^>/]*)?>', '</([a-zA-Z]*?)>'], # HTML tags, e.g. <div width="2px"> </div>
]

# Some pages are expected to have mismatched parenthesis (as they are part of the update history, item description, etc)
exemptions = {
  'Advanced_Weaponiser': pairs[5],      # Includes example console commands
  'Bots': pairs[5],                     # Includes example console commands 
  'Linux dedicated server': pairs[0],   # Includes a bash script with case
  'List_of_default_keys': pairs[2],     # Includes {{Key|]}}
  'List_of_useful_console_commands': pairs[5], # Includes placeholder <>
  'Uber Update': pairs[0],              # The update notes include 1) 2)
}

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']
PAGESCRAPERS = 50

# For regex matches which have a group, we want to include the group contents, so that we can compare pairs of HTML tags.
# For pure punctuation matches, we don't need any comparison.
def get_match_info(m):
  groups = m.groups()
  if len(groups) == 0:
    return None
  else:
    return groups[0].lower()

def pagescraper(pages, done, translation_data):
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  while True:
    try:
      page = Page(w, pages.get(True, 1)['title'])
    except Empty:
      if done.is_set():
        return
      else:
        continue

    text = page.get_wiki_text()
    errors = []
    for i, pair in enumerate(pairs):
      locations = []
      if pair in exemptions.get(page.base, []):
        continue

      for m in finditer(pair[0], text):
        match_info = get_match_info(m)
        if match_info == 'br':
          continue # The <br> tag is self-contained, and does not need a matching </br>
        locations.append([m.start(), +1, match_info])

      for m in finditer(pair[1], text):
        match_info = get_match_info(m)
        if match_info == 'br':
          continue # The </br> tag is self-contained, and does not need a matching <br>
        locations.append([m.start(), -1, match_info])

      locations.sort()

      opens = []
      for index, val, contents in locations:
        if val == +1:
          opens.append([index, contents])
        elif val == -1:
          if len(opens) == 0:
            errors.append(index) # Closing tag without a matching opening
          elif opens[-1][1] != contents: # Mismatched HTML tag
            errors.append(index) # Mark the closing tag, hopefully not too confusing if it was actually the open tag's fault
          else:
            opens.pop() # Matching

      for extra_open in opens:
        errors.append(extra_open[0]) # Opening tags without a matching closing

    if len(errors) > 0:
      if verbose:
        print(f'Found {len(errors)} errors for page {page.title}')
      data = f'<h3> [{page.get_edit_url()} {page.title}] </h3>\n'
      errors.sort()
      for error in errors:
        # For display purposes, we want to highlight the mismatched symbol. To do so, we replicate the symbol on the line below, at the same horizontal offset.
        # For sanity reasons, we don't want to show too long of a line.

        start = text.rfind('\n', error-60, error) # Find the start of the line (max 80 chars behind)
        if start == -1:
          start = max(0, error-60) # Not found
        else:
          start += 1 # We don't actually want to include the \n

        # Find the next EOL, potentially including >1 line if EOL is within 20 characters.
        end = text.find('\n', start+10, start+120)
        if end == -1:
          end = start+120

        # Compute additional padding for wide characters
        widths = [width(char) for char in text[start:error]]
        extra_width = widths.count('W') # + widths.count('F')

        data += '<div class="mw-code"><nowiki>\n'
        data += text[start:end] + '\n'
        extra_width = int(widths.count('W') * 0.8) # ... a guess
        data += ' '*(error-start+extra_width) + text[error] + '\n'
        data += '</nowiki></div>\n'
      if page.lang in LANGS:
        translation_data[page.lang].append(data)
      else:
        translation_data['en'].append(data)

def main():
  pages, done = Queue(), Event()
  translation_data = {lang: [] for lang in LANGS}
  threads = []
  for _ in range(PAGESCRAPERS): # Number of threads
    thread = Thread(target=pagescraper, args=(pages, done, translation_data))
    threads.append(thread)
    thread.start()
  try:
    w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
    for page in w.get_all_pages():
      pages.put(page)

  finally:
    done.set()
    for thread in threads:
      thread.join()

  output = """\
{{{{DISPLAYTITLE: {count} pages with mismatched parenthesis}}}}
Pages with mismatched <nowiki>(), [], and {}</nowiki>. Data as of {date}.
{{{{TOC limit|2}}}}

""".format(
    count=sum(len(lang_pages) for lang_pages in translation_data.values()),
    date=strftime(r'%H:%M, %d %B %Y', gmtime()))

  for language in LANGS:
    if len(translation_data[language]) > 0:
      output += '== {{lang name|name|%s}} ==\n' % language
      for data in translation_data[language]:
        output += data

  return output

if __name__ == '__main__':
  verbose = True
  f = open('wiki_mismatched_parenthesis.txt', 'w', encoding='utf-8')
  f.write(main())
  print('Article written to wiki_mismatched_parenthesis.txt')
  f.close()

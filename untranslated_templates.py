from queue import Empty, Queue
from threading import Thread, Event
from re import compile, IGNORECASE, VERBOSE
from time import gmtime, strftime
from wikitools import wiki
from wikitools.page import Page

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']
PAGESCRAPERS = 50

LANG_TEMPLATE_START = compile("""\
  [^{]{{    # The start of a template '{{' which is not the start of a parameter '{{{'
  \s*       # Any amount of whitespace is allowed before the template name
  lang      # Language template. Note that this does not allow invocations of {{lang incomplete}}
  \s*       # Any amount of whitespace (but critically, no more ascii characters)
  \|        # Start of parameter list
""", IGNORECASE | VERBOSE)

LANG_TEMPLATE_ARGS = compile("""\
  \|        # Start of a parameter
  (
    [^=]*?  # Key name
  )
  =         # Start of a value
""", VERBOSE)

def pagescraper(pages, done, translations, usage_counts):
  while True:
    try:
      page = pages.get(True, 1)
    except Empty:
      if done.is_set():
        return
      else:
        continue

    page_text = page.get_wiki_text()
    # First, find the matching pairs
    def get_indices(char, string):
      index = -1
      indices = []
      while 1:
        try:
          index = string.index(char, index+1)
        except ValueError:
          break
        indices.append(index)
      return indices

    locations = [[len(page_text), -1]]
    for open in get_indices('{', page_text):
      locations.append([open, 1])
    for close in get_indices('}', page_text):
      locations.append([close, -1])
    locations.sort()

    # Next, divide the text up based on those pairs. Embedded text is separated out, e.g. {a{b}c} will become "ac" and "b".
    stack = [0]
    buffer = {0: ''}
    lastIndex = 0
    for index, value in locations:
      try:
        buffer[stack[-1]] += page_text[lastIndex:index]
      except KeyError: # New addition
        buffer[stack[-1]] = page_text[lastIndex:index]
      except IndexError: # Unmached parenthesis, e.g. Class Weapons Tables
        buffer[0] += page_text[lastIndex:index] # Add text to default layer
        stack.append(None) # So there's something to .pop()
        if verbose:
          print('Found a closing brace without a matched opening brace')
      if value == 1:
        stack.append(index)
      elif value == -1:
        stack.pop()
      lastIndex = index + 1

    if verbose:
      print(page.title, 'contains', len(buffer), 'pairs of braces')

    missing_languages = []
    # Finally, search through for lang templates using regex
    for match in LANG_TEMPLATE_START.finditer(page_text):

      this_missing_languages = set(LANGS)
      for match2 in LANG_TEMPLATE_ARGS.finditer(buffer[match.start() + 2]):
        language = match2.group(1).strip().lower()
        this_missing_languages.discard(language)
      missing_languages += this_missing_languages

    if len(missing_languages) > 0:
      if verbose:
        actually_missing = sorted(set(missing_languages))
        print(f'{page.title} is not translated into {len(actually_missing)} languages:', ', '.join(actually_missing))

      usage_count = page.get_transclusion_count()
      if usage_count == 0:
        continue
      usage_counts[page.title] =  usage_count
      for lang in LANGS:
        translations[lang].append((page, missing_languages.count(lang)))

def main(w):
  pages, done = Queue(), Event()
  translations = {lang: [] for lang in LANGS}
  usage_counts = {}
  threads = []
  for _ in range(PAGESCRAPERS): # Number of threads
    thread = Thread(target=pagescraper, args=(pages, done, translations, usage_counts))
    threads.append(thread)
    thread.start()
  try:
    for page in w.get_all_templates():
      if '/' in page.title:
        continue # Don't include subpage templates like Template:Dictionary and Template:PatchDiff
      if page.title[:13] == 'Template:User':
        continue # Don't include userboxes
      if page.title == 'Template:Lang':
        continue # Special exclusion
      pages.put(page)

  finally:
    done.set()
    for thread in threads:
      thread.join()

  outputs = []
  for language in LANGS:
    output = """\
{{{{DISPLAYTITLE: {count} templates missing {{{{lang name|name|{lang}}}}} translation}}}}
Pages missing in {{{{lang info|{lang}}}}}: '''<onlyinclude>{count}</onlyinclude>''' in total. Data as of {date}.

; See also
* [[TFW:Reports/All articles/{lang}|All articles in {{{{lang name|name|{lang}}}}}]]
* [[TFW:Reports/Missing translations/{lang}|Missing article translations in {{{{lang name|name|{lang}}}}}]]
* [[Special:RecentChangesLinked/Project:Reports/All articles/{lang}|Recent changes to articles in {{{{lang name|name|{lang}}}}}]]

== List ==""".format(
      lang=language,
      count=len(translations[language]),
      date=strftime(r'%H:%M, %d %B %Y', gmtime()))

    for template, missing in sorted(translations[language], key=lambda elem: -usage_counts[elem[0].title]):
      output += f'\n# [{template.get_edit_url()} {template.title} has {usage_counts[template.title]} uses] and is missing {missing} translations'
    outputs.append([language, output])
  return outputs

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_untranslated_templates.txt', 'w') as f:
    for lang, output in main(w):
      f.write('\n===== %s =====\n' % lang)
      f.write(output)
  print(f'Article written to {f.name}')

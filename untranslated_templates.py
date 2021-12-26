from queue import Empty, Queue
from threading import Thread, Event
from re import finditer, DOTALL
from time import gmtime, strftime
from wikitools import wiki
from wikitools.page import Page

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']
PAGESCRAPERS = 50

def pagescraper(w, pages, done, translations):
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
      except KeyError: #
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

    missing_languages = set()
    # Finally, search through for lang templates via positive lookahead
    for match in finditer('{(?=(.*?)\|)', page_text, DOTALL):
      template = match.group(1).strip().lower()
      languages = []
      if template == 'lang': # And count out their params
        if page_text[match.start()-2:match.start()+1] == '{{{':
          continue # Skip any parameters named lang, viz.: {{{lang|}}}
        for match2 in finditer('\|(.*?)=', buffer[match.start()]):
          languages.append(match2.group(1).strip().lower())
        for language in translations:
          if language not in languages: # Add missing translations
            translations[language].add(page.title)
            missing_languages.add(language)
    if len(missing_languages) > 0:
      if verbose:
        print(page.title, 'is not translated into', len(missing_languages), 'languages:', ', '.join(missing_languages))

def main(w):
  pages, done = Queue(), Event()
  translations = {lang: set() for lang in LANGS}
  threads = []
  for _ in range(PAGESCRAPERS): # Number of threads
    thread = Thread(target=pagescraper, args=(w, pages, done, translations))
    threads.append(thread)
    thread.start()
  try:
    for page in w.get_all_templates():
      if '/' in page.title:
        continue # Don't include subpage templates like Template:Dictionary and Template:PatchDiff
      if page.title[:13] == 'Template:User':
        continue # Don't include userboxes
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
    for template in sorted(translations[language]):
      output += f'\n# [[{template}]]'
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

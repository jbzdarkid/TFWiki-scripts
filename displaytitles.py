from queue import Queue, Empty
from re import search
from threading import Thread, Event
from time import gmtime, strftime
from wikitools import wiki

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']
PAGESCRAPERS = 50

def pagescraper(pages, done, errors, overflow):
  while True:
    try:
      page = pages.get(True, 1)
    except Empty:
      if done.is_set():
        return
      else:
        continue

    if __name__ != '__main__': 
      # When running as part of automation, wiki text will be cached, so it is faster to query the wikitext
      # before making another network call to get the page source.
      wikitext = page.get_wiki_text()
      if 'DISPLAYTITLE' not in wikitext:
        continue

    html = page.get_raw_html()
    m = search('<span class="error">(.*?)</span>', html)
    if not m:
      continue
    if 'Display title' in m.group(0):
      errors.append(page)
    else:
      overflow[m.group(1)] = page

def main(w):
  pages, done = Queue(), Event()
  errors = []
  overflow = {}
  threads = []
  for _ in range(PAGESCRAPERS): # Number of threads
    thread = Thread(target=pagescraper, args=(pages, done, errors, overflow))
    threads.append(thread)
    thread.start()
  try:
    for page in w.get_all_pages():
      pages.put(page)

  finally:
    done.set()
    for thread in threads:
      thread.join()

  duplicate_errors = {lang: [] for lang in LANGS}
  for page in errors:
    lang = page.title.rpartition('/')[2]
    if lang not in LANGS:
      lang = 'en'
    duplicate_errors[lang].append(page)

  output = """\
{{{{DISPLAYTITLE: {count} pages with duplicate DISPLAYTITLEs}}}}
<onlyinclude>{count}</onlyinclude> pages with two (or more) display titles. Data as of {date}.
{{{{TOC limit|2}}}}

""".format(
    count=len(errors),
    date=strftime(r'%H:%M, %d %B %Y', gmtime()))

  if len(overflow) > 0:
    output += '== Other errors ==\n'
    for error, page in overflow.items():
      output += f'=== [[{page.title}]] ===\n{error}\n'

  for language in LANGS:
    if len(duplicate_errors[language]) > 0:
      output += '== {{lang name|name|%s}} ==\n' % language
      for page in duplicate_errors[language]:
        output += f'* [{page.get_edit_url()} {page.title}]\n'
  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_mismatched_parenthesis.txt', 'w', encoding='utf-8') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

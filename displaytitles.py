from re import search
from utils import pagescraper_queue, time_and_date
from wikitools import wiki

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

def pagescraper(page, errors, disambig_errors, overflow):
  if __name__ != '__main__':
    # When running as part of automation, wiki text will be cached, so it is faster to query the wikitext
    # before making another network call to get the page source.
    # ... but this prevents finding other errors
    wikitext = page.get_wiki_text()
    if 'DISPLAYTITLE' not in wikitext:
      return

  html = page.get_raw_html()
  m = search('<span class="error">(.*?)</span>', html)
  if not m:
    return
  if verbose:
    print(f'Page {page.title} has an error: {m.group(0)}')
  if 'Display title' in m.group(0):
    if '<a href="/wiki/Category:Disambiguation' in html:
      disambig_errors[page.lang].append(page)
    else:
      errors[page.lang].append(page)
  else:
    overflow[m.group(1)] = page

def main(w):
  errors = {lang: [] for lang in LANGS}
  disambig_errors = {lang: [] for lang in LANGS}
  overflow = {}
  with pagescraper_queue(pagescraper, errors, disambig_errors, overflow) as pages:
    for page in w.get_all_pages(namespaces=['Main', 'TFW', 'File', 'Template', 'Help', 'Category']):
      pages.put(page)

  num_pages = sum(len(pages) for pages in errors.values()) +
              sum(len(pages) for pages in disambig_errors.values()) +
              len(overflow)
  if verbose:
    print(f'Found {num_pages} pages with errors')

  output = """\
{{{{DISPLAYTITLE: {count} pages with duplicate DISPLAYTITLEs}}}}
<onlyinclude>{count}</onlyinclude> pages with two (or more) display titles. Data as of {date}.
{{{{TOC limit|2}}}}

""".format(
    count=num_pages,
    date=time_and_date())

  if len(overflow) > 0:
    output += '== Other errors ==\n'
    for error, page in overflow.items():
      output += f'=== [[{page.title}]] ===\n{error}\n'

  for language in LANGS:
    if len(errors[language]) > 0:
      output += '== {{lang name|name|%s}} ==\n' % language
      for page in sorted(errors[language]):
        output += f'* [[{page.title}]]\n'
    if len(disambig_errors[language]) > 0:
      output += '=== Disambiguation pages ===\n' % language
      for page in sorted(disambig_errors[language]):
        output += f'* [[{page.title}]]\n'
  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_displaytitles.txt', 'w', encoding='utf-8') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

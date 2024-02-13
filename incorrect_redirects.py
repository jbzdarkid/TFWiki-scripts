from utils import pagescraper_queue, time_and_date
from wikitools import wiki
from wikitools.page import Page

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']
NAMESPACES = ['Main', 'TFW', 'Help', 'Category']

def pagescraper(page, english_redirects, lang_redirects, bad_redirects):
  link = next(page.get_links(namespaces=NAMESPACES), None)
  if not link:
    if verbose:
      print(f'{page.title} redirects to a page outside of NAMESPACES, ignoring')
    return

  if page.lang == 'en':
    english_redirects[page.title] = link
  elif page.lang != link.lang:
    bad_redirects[page.lang][page] = link
  else:
    lang_redirects[page.lang][page] = link

def main(w):
  english_redirects = {}
  lang_redirects = {language: {} for language in LANGS}
  bad_redirects = {language: {} for language in LANGS}
  with pagescraper_queue(pagescraper, english_redirects, lang_redirects, bad_redirects) as pages:
    for page in w.get_all_pages(namespaces=NAMESPACES, redirects=True):
      pages.put(page)

  incorrect_redirects = {language: set() for language in LANGS}
  for language in LANGS:
    for page in sorted(lang_redirects[language].keys()):
      if page.basename not in english_redirects:
        if verbose:
          print(f'{page.title} does not correspond to an english redirect')
        continue
      
      lang_target = lang_redirects[language][page]
      english_target = english_redirects[page.basename]

      if lang_target.basename != english_target.basename:
        incorrect_redirects[language].add(page)

  output = """\
{{{{DISPLAYTITLE: {count} pages with different redirects from english}}}}
'''<onlyinclude>{count}</onlyinclude>''' translated redirects which go somewhere else from their corresponding english redirect. Data as of {date}.

""".format(
      count=sum((len(incorrect_redirects[lang]) for lang in LANGS)),
      date=time_and_date())

  if len(bad_redirects) > 0:
    output += '== Cross-language redirects ==\n'
    for language in LANGS:
      if len(bad_redirects[language]) == 0:
        continue

      output += '=== {{lang name|name|%s}} ===\n' % language
      for page in sorted(bad_redirects[language]):
        target = bad_redirects[language][page]
        output += '* [%s&redirect=no %s] redirects to [[%s]]\n' % (page.get_page_url(), page.title, target)

  output += '== Mis-translated redirects ==\n'
  for language in LANGS:
    if len(incorrect_redirects[language]) == 0:
      continue

    output += '=== {{lang name|name|%s}} ===\n' % language
    for page in sorted(incorrect_redirects[language]):
      lang_target = lang_redirects[language][page]
      english_target = english_redirects[page.basename]
      output += '* [%s&redirect=no %s] redirects to [[%s]] but' % (page.get_page_url(), page.title, lang_target)
      output += ' [%s&redirect=no %s] redirects to [[%s]]\n' % (Page(w, page.basename).get_page_url(), page.basename, english_target)

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_incorrect_redirects.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

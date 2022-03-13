from re import compile
from utils import pagescraper_queue, time_and_date
from wikitools import wiki

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']
namespaces = ['Main', 'TFW', 'Help', 'Category']

def pagescraper(page, mislinked):
  links = []
  for namespace in namespaces:
    for link in page.get_links(namespace=namespace):
      if page.basename == 'Localization files' and link.basename == 'Winger':
        continue # Used as a cross-language example for localization files
      elif page.basename == 'Spy' and link.basename in ['Spy responses', 'Spy voice commands']:
        continue # Used as a piece of trivia
      elif link.lang == 'en':
        continue # There are *countless* places where a link is untranslated. Accounting for all of them is foolish.
      elif link.lang != page.lang:
        links.append(link.title)

  if len(links) > 0:
    if verbose:
      print(f'Found {len(links)} bad links on {page}')
    mislinked[page.lang].append([page, links])

def main(w):
  mislinked = {lang: [] for lang in LANGS}
  with pagescraper_queue(pagescraper, mislinked) as pages:
    for page in w.get_all_pages(namespaces=namespaces):
      if page.basename in ['Main Page', 'Main Page (Classic)']:
        continue # Main Page links to all other main pages
      pages.put(page)

  page_count = sum(len(pages) for pages in mislinked.values())
  output = f"""\
{{{{DISPLAYTITLE: {page_count} pages with bad links}}}}
<onlyinclude>{page_count}</onlyinclude> pages link to pages in other (non-english) languages. Data as of {time_and_date()}.
"""

  for language in LANGS:
    if len(mislinked[language]) == 0:
      continue

    if verbose:
      print(f'{len(mislinked)} pages with bad links')

    output += '== {{lang name|name|%s}} ==\n' % language
    for page, links in sorted(mislinked[language]):
      output += f'* [{page.get_edit_url()} {page.title}] has {len(links)} link{"s"[:len(links)^1]} to other languages: '
      bad_links = [f'[[{link}]]' for link in sorted(links)]
      output += ', '.join(bad_links) + '\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_incorrectly_linked.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

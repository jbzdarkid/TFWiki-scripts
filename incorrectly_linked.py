from re import compile
from utils import pagescraper_queue, time_and_date
from wikitools import wiki

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']
link_regex = compile(r'\[\[([^\]|]+)')

def pagescraper(page, w, mislinked):
  links = []
  for link in page.get_links():
    if link.lang != page.lang and link.lang != 'en':
      links.append(link.title)

  if len(links) > 0:
    if verbose:
      print(f'Found {len(links)} bad links on {page}') 
    mislinked[page.lang].append([page, links])

def main(w):
  mislinked = {lang: [] for lang in LANGS}
  with pagescraper_queue(pagescraper, w, mislinked) as pages:
    for page in w.get_all_pages():
      pages.put(page)

  output = f"""\
{{{{DISPLAYTITLE: {page_count} pages with bad links}}}}
{page_count} pages link to pages in other languages. Data as of {time_and_date()}.
""".format(
    page_count=sum(len(pages) for pages in mislinked.values()))

  for language in LANGS:
    if len(mislinked[language]) == 0:
      continue

    if verbose:
      print(f'{len(mislinked)} pages with bad links')

    output += '== {{lang name|name|%s}} ==\n' % language
    for page, links in sorted(mislinked[language]):
      output += f'* [{page.get_edit_url()} {page.title}] has {len(links)} links to other languages:\n'
      output += ', '.join('[[{link}]]' for link in links) + '\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_incorrectly_linked.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

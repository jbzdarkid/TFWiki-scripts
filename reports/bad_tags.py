from .utils import pagescraper_queue, time_and_date
from wikitools import wiki

verbose = False

def pagescraper(page, usage):
  text = page.get_wiki_text()
  for tag in ['noinclude', 'includeonly', 'onlyinclude']:
    if f'<{tag}>' in text or f'</{tag}>' in text:
      if verbose:
        print(f'Page {page.title} uses <{tag}>')
      transclusions = page.get_transclusion_count(namespaces=['Main', 'Help', 'TFW'])
      if transclusions > 0:
        if verbose:
          print(f'Page {page.title} allowed; it is transcluded on {transclusions} pages')
        continue
      usage[tag][page] = transclusions

def main(w):
  usage = {'noinclude': {}, 'includeonly': {}, 'onlyinclude': {}}
  with pagescraper_queue(pagescraper, usage) as pages:
    for page in w.get_all_pages(namespaces=['Main', 'Help', 'TFW']):
      pages.put(page)

  output = """\
{{{{DISPLAYTITLE: {count} non-template pages which are using template-only tags}}}}
Found '''<onlyinclude>{count}</onlyinclude>''' pages which are using HTML tags that are reserved for templates. Data as of {date}.

""".format(
    count=sum((len(pages) for pages in usage.values())),
    date=time_and_date())

  for tag, pages in usage.items():
    if pages:
      output += f'== <nowiki>{tag}</nowiki> ==\n'
      for page in sorted(pages.keys(), key = lambda page: page.url_title):
        output += f'* [{page.get_edit_url()} {page.title}]\n'

  return output

if __name__ == '__main__':
  import os
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php', user_agent=os.environ['USER_AGENT'])
  with open('wiki_bad_tags.txt', 'w', encoding='utf-8') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

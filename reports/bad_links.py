from collections import defaultdict
from re import finditer
from .utils import pagescraper_queue_single, time_and_date
from wikitools import wiki

verbose = False

def pagescraper(page, links, anchors):
  html = page.get_raw_html()
  for m in finditer('<a href="/wiki/(.*?)#(.*?)"', html):
    target = m.group(1)
    section = m.group(2)
    links[target][section].append(page)

  for m in finditer('<span .*?id="(.*?)"', html):
    anchors[page].append(m.group(1))

def main(w):
  links = defaultdict(lambda: defaultdict(list))
  anchors = defaultdict(list)

  with pagescraper_queue_single(pagescraper, links, anchors) as pages:
    for page in w.get_all_pages(namespaces=['Main', 'TFW', 'File', 'Template', 'Help', 'Category']):
      pages.put(page)

  broken_links = defaultdict(lambda: defaultdict(list))
  for target in links:
    for section in links[target]:
      if section in anchors[target]:
        for source in links[target][section]:
          broken_links[source.lang][source].append((target, section))

  output = """\
{{{{DISPLAYTITLE: {count} pages with broken subsection links}}}}
<onlyinclude>{count}</onlyinclude> pages which link to a nonexistant subsection on another page. Data as of {date}.

""".format(
    count=sum(len(v) for v in broken_links.values()),
    date=time_and_date())


  for lang in broken_links:
    output += '== {{lang name|name|%s}} ==\n' % lang
    for page in sorted(broken_links[lang]):
      output += f'=== [[{page.title}]] ===\n'
      for target, section in broken_links[lang][page]:
        output += f'* [[{target}#{section}]]'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_bad_links.txt', 'w', encoding='utf-8') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

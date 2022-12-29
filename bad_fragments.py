from re import compile, VERBOSE
from utils import pagescraper_queue, time_and_date
from wikitools import wiki

verbose = False

# Within the HTML source code, all links should be href="()". Internal links start with /wiki/foo, so this will find all external links.
LINK_REGEX = compile('''
  href="/wiki/ # Within the HTML source code, all wiki links are href="/wiki/..."
  ([^?#"]*)    # 1: Title
  \\#([^"]*)   # 2: Fragment
  "
''', VERBOSE)

ANCHOR_REGEX = compile('<span class="mw-headline" id="([^"]*)">')

def pagescraper(page, links, sections):
  text = page.get_raw_html()

  page_links = []
  page_sections = []

  for m in LINK_REGEX.finditer(text):
    page_links.append((m[1], m[2]))

  for m in ANCHOR_REGEX.finditer(text):
    anchor = m[1]
    page_sections.append(anchor)

  links[page.title] = page_links
  sections[page.title] = page_sections


def main(w):
  # First, get all of the page contents to find links and section headers
  links = {}
  sections = {}
  with pagescraper_queue(pagescraper, links, sections) as pages:
    for page in w.get_all_pages():
      pages.put(page)

  total_bad_links = 0
  bad_links = {}
  for page, page_links in links.items():
    bad_page_links = []
    for target_page, target_section in page_links:
      if target_page in sections and target_section not in sections[target_page]:
        bad_page_links.append((target_page, target_section))
        total_bad_links += 1
    if len(bad_page_links) > 0:
      bad_links[page] = bad_page_links

  output = """\
{{{{DISPLAYTITLE: {total_bad_links} links to nonexistant section headings}}}}
There are <onlyinclude>{total_bad_links}</onlyinclude> links from {bad_pages} pages which do not link to valid subsections. Data as of {date}.

{{{{TOC limit|3}}}}
""".format(
    total_bad_links=total_bad_links,
    bad_pages=len(bad_links),
    date=time_and_date())

  for page in sorted(bad_links.keys()):
    output += f'== [[{page}]] ==\n'
    for target_page, target_section in sorted(bad_links[page]):
      output += f'* [[{target_page}#{target_section}]]\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_bad_redirects.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

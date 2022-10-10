from re import compile, VERBOSE
from utils import pagescraper_queue, time_and_date
from wikitools import wiki

verbose = False

# Within the HTML source code, all links should be href="()". Internal links start with /wiki/foo, so this will find all external links.
LINK_REGEX = compile('''
  href="       # Within the HTML source code, all links are href="..."
  ([^:]*://)   # 1: Scheme
  ([^/?#"]+)   # 2: Domain
  (/[^?#"]*)   # 3: Path
  (\\?[^#"]*)? # 4: Query (optional)
  (\\#[^"]*)?    # 5: Fragment (optional)
  "
''', VERBOSE)

ANCHOR_REGEX = compile('<span class="mw-headline" id="([^"]*)">')

def get_wiki_link(m):
  domain = m[1]
  if domain == 'wiki.teamfortress.com':
    fragment = m[5]
    if fragment:
      query = m[4]
      for part in query[1:].split('&'):
        key, value = part.split('=', 1)
        if key == 'title':
          return (key, fragment)

  return None, None


def pagescraper(page, links, sections):
  text = page.get_raw_html()

  page_links = []
  page_sections = []

  for m in LINK_REGEX.finditer(text):
    link_title, fragment = get_wiki_link(m)
    if link_title:
      page_links.append((link_title, fragment))

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
      if target_section not in sections[target_page]:
        bad_page_links.append((target_page, target_section))
        total_bad_links += 1
    if len(bad_page_links) > 0:
      bad_links[page] = bad_page_links

  output = """\
{{{{DISPLAYTITLE: {total_bad_links} links to nonexistant section headings}}}}
Found <onlyinclude>{total_bad_links}</onlyinclude> links from {bad_pages} which do not link to valid . Data as of {date}.

{{{{TOC limit|3}}}}
""".format(
    total_bad_links=total_bad_links,
    bad_pages=len(bad_links),
    date=time_and_date())

  for page in sorted(bad_links.keys()):
    output += f'== {page} ==\n'
    for target_page, target_section in sorted(bad_links[page]):
      output += f'* {page} links to {target_page}#{target_section}, which doesn\'t exist.\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_bad_redirects.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

from re import compile, VERBOSE
from utils import pagescraper_queue
from wikitools import wiki

verbose = False

# Within the HTML source code, all links should be href="()". Internal links start with /wiki/foo, so this will find all external links.
LINK_REGEX = compile('''
  href="(       # Within the HTML source code, all links start with href=
    (           # Start inner capture group (for just the domain name)
      https?:// # Match http/https scheme (internal wiki links start with /wiki)
      [^/"]+    # The domain
    )
    [^"]*       # The rest of the URL
  )"
''', VERBOSE)

def pagescraper(page, all_links):
  text = page.get_raw_html()

  for m in LINK_REGEX.finditer(text):
    domain = m[2]
    link = m[1]
    if domain not in all_links:
      if domain not in all_links:
        all_links[domain] = {}
      if link not in all_links[domain]:
        all_links[domain][link] = []
      all_links[domain][link].append(page) 

def main(w):
  page_links = {} # Map of page: {links}
  with pagescraper_queue(pagescraper, all_links) as pages:
    for page in w.get_all_pages():
      pages.put(page)

  output = '{{DISPLAYTITLE: TEST ONLY REPORT}}\n{{TOC limit|2}}\n'

  for domain in sorted(all_links.keys()):
    output += f'== {domain} ==\n'
    for link in sorted(all_links[domain].keys()):
      output += f'=== {link} ===\n'
      for page in sorted(all_links[domain][link])[:10]:
        output += f'* [[page]]\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_all_external_links.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')


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
    domain = '.'.join(m[2].split('.')[-2:])
    link = m[1]
    if domain not in all_links:
      if domain not in all_links:
        all_links[domain] = {}
      if link not in all_links[domain]:
        all_links[domain][link] = []
      all_links[domain][link].append(page)

def main(w):
  all_links = {}
  with pagescraper_queue(pagescraper, all_links) as pages:
    for page in w.get_all_pages():
      pages.put(page)

  output = '{{DISPLAYTITLE: TEST ONLY REPORT}}\n{{TOC limit|2}}\n'

  # Avoid rendering images inline
  def link_escape(link):
    if (
      'tinyurl' in link or
      link.endswith('.png') or
      link.endswith('.jpg') or
      link.endswith('.gif')
    ):
      return link.replace('/', '&#47;')
    return link

  # Sort domains by the total number of links on all pages.
  domains = [(
    sum(len(links) for links in domain_links.values()),
    domain, 
  ) for domain, domain_links in all_links.values()]
  for total_links, domain in sorted(domains):
    output += f'== {domain} ({total_links}) ==\n'
    for link in sorted(all_links[domain].keys()):
      # Only print one link, but list the count
      output += f'=== {link_escape(link)} ({len(all_links[domain][link])}) ===\n'
      output += f'* [[{all_links[domain][link][0]}]]\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_all_external_links.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

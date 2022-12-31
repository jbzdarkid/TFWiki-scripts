from re import compile, VERBOSE
from utils import pagescraper_queue, plural
from wikitools import wiki

verbose = False

# Within the HTML source code, all links should be href="()". Internal links start with /wiki/foo, so this will find all external links.
LINK_REGEX = compile('''
  href="(       # Within the HTML source code, all links start with href=
    https?://   # Match http/https scheme (internal wiki links start with /wiki)
    (           # Start inner capture group (for just the domain name)
      [^/"]+    # The domain
    )
    [^"]*       # The rest of the URL
  )"
''', VERBOSE)

# Domains which cannot be malware or phishing or broken links. Hopefully.
safe_hosts = [
  'wikipedia.org',
  'steamcommunity.com',
  'steampowered.com',
  'teamfortress.com',
]

def pagescraper(page, all_links):
  text = page.get_raw_html()

  for m in LINK_REGEX.finditer(text):
    hostname = '.'.join(m[2].split('.')[-2:])
    if hostname in safe_hosts:
      continue
    link = m[1]

    if hostname not in all_links:
      all_links[hostname] = {}
    if link not in all_links[hostname]:
      all_links[hostname][link] = []
    all_links[hostname][link].append(page)

def main(w):
  all_links = {} # Map of {domain: {link: [pages]}}
  with pagescraper_queue(pagescraper, all_links) as pages:
    i = 0
    for page in w.get_all_pages():
      i += 1
      if i > 1000:
        break
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

  # Sort domains by the total number pages which link to that domain (i.e. the blast radius)
  domains = []
  for domain in all_links:
    domain_pages = set()
    for link in all_links[domain]:
      for page in all_links[domain][link]:
        domain_pages.add(page.title)
    domains.append((len(domain_pages), domain))
  domains.sort()

  for total_pages, domain in domains:
    output += f'== {domain} ({plural.pages(total_pages)}) ==\n'
    # Print out each link, and the count of pages that use it
    for link in sorted(all_links[domain].keys()):
      pages_per_link = len(all_links[domain][link])
      output += f'* {link_escape(link)} ({plural.pages(pages_per_link)})\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_all_external_links.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

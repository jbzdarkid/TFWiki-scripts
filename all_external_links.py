from re import compile, VERBOSE
from utils import pagescraper_queue, plural, time_and_date
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

def pagescraper(page, all_links):
  text = page.get_raw_html()

  for m in LINK_REGEX.finditer(text):
    hostname = '.'.join(m[2].split('.')[-2:]).lower()
    if hostname not in all_links:
      all_links[hostname] = set()
    all_links[hostname].add(page)

def main(w):
  all_links = {} # Map of {domain: {link: [pages]}}
  with pagescraper_queue(pagescraper, all_links) as pages:
    for page in w.get_all_pages():
      pages.put(page)

  output = """\
{{{{DISPLAYTITLE: {domain_count} external domains}}}}
There are external links to <onlyinclude>{domain_count}</onlyinclude> different domains from the wiki. Data as of {date}.

{{{{TOC limit|2}}}}
""".format(
    domain_count=len(all_links),
    date=time_and_date())

  domains = list(all_links.keys())
  domains.sort(key = lambda domain: len(all_links[domain]))

  for domain in domains:
    # Sort pages by language, then title (with english first)
    pages = list(all_links[domain])
    pages.sort(key = lambda page: (page.lang == 'en', page.lang, page.title))

    output += f'== {domain} ({plural.pages(len(pages))}) ==\n'
    for page in pages[:10]:
      output += f'* [[{page.title}]]\n'
    if len(pages) > 10:
      output += f'... and {len(pages)-10} more\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_all_external_links.txt', 'w', encoding='utf-8') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

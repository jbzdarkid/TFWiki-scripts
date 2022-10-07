from os import environ
from re import compile, VERBOSE
from time import sleep
from utils import pagescraper_queue, time_and_date
from wikitools import wiki
import requests

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

# Domains which cannot be malware or phishing or broken links. Hopefully.
safe_domains = [
  'http://en.wikipedia.org',
  'http://steamcommunity.com',
  'http://store.steampowered.com',
  'http://www.teamfortress.com',
  'https://en.wikipedia.org',
  'https://steamcommunity.com',
  'https://wiki.teamfortress.com',
  'https://www.teamfortress.com',
]

def pagescraper(page, page_links, all_domains, all_links):
  text = page.get_raw_html()

  links = set()
  for m in LINK_REGEX.finditer(text):
    domain = m.group(2)
    if domain in safe_domains:
      continue
    link = m.group(1)

    links.add(link)
    all_domains.add(domain)
    if domain not in all_links:
      all_links[domain] = set()
    all_links[domain].add(link)
  page_links[page] = links

  if verbose:
    print(f'Scraped a total of {len(links)} unique links from {page.title}')

def safely_request(verb, url, *, timeout=20, retry=True):
  try:
    r = requests.request(verb, url, timeout=timeout, headers={'User-Agent': 'TFWiki-scripts/0.1 (https://wiki.tf/u/DarkBOT; https://github.com/jbzdarkid/TFWiki-scripts/issues)'})
  except requests.exceptions.ConnectionError:
    return '404 NOT FOUND'
  except requests.exceptions.Timeout:
    return '504 GATEWAY TIMEOUT'
  except requests.exceptions.TooManyRedirects:
    return '508 LOOP DETECTED'
  except requests.exceptions.ChunkedEncodingError:
    return '418 I\'M A TEAPOT'

  if r.is_redirect:
    return '508 LOOP DETECTED'
  elif r.status_code == 429 and retry:
    sleep(5) # There are more precise options but this should be fine for a single retry.
    return safely_request(verb, url, timeout=timeout, retry=False)
  elif r.status_code == 503 and '://amazon.com' in url:
    # Amazon has some pretty heavy rate-limiting (for anti-compete reasons) when we scrape their pages.
    return None # So don't report these as failures.
  elif not r.ok:
    return f'{r.status_code} {r.reason.upper()}'
  return None # no error, we don't actually care about the response text

def domain_verifier(domains, dead_domains, dangerous_domains):
  json = {
    'client': {'clientId': 'github.com/jbzdarkid/TFWiki-scripts', 'clientVersion': '1.0'},
    'threatInfo': {
      'threatTypes': ['MALWARE', 'SOCIAL_ENGINEERING', 'UNWANTED_SOFTWARE', 'POTENTIALLY_HARMFUL_APPLICATION'],
      'platformTypes': ['ANY_PLATFORM'],
      'threatEntryTypes': ['URL'],
      'threatEntries': [{'url': domain} for domain in domains],
    }
  }

  r = requests.post('https://safebrowsing.googleapis.com/v4/threatMatches:find?key=' + environ['API_KEY'], json=json)
  j = r.json()
  if matches := j.get('matches'):
    for match in matches:
      domain = match['threat']['url']
      dangerous_domains[domain] = match['threatType'].replace('_', ' ').title()

  # TODO: WHOIS lookups for domains.
  # https://www.iana.org/domains/root/db

def link_verifier(links, dead_links):
  for link in links:
    if reason := safely_request('GET', link):
      dead_links[link] = reason

def main(w):
  # First, scrape all the links from all of the pages
  page_links = {} # Map of page: {links}
  all_domains = set()
  all_links = {} # Map of domain: {links}
  with pagescraper_queue(pagescraper, page_links, all_domains, all_links) as pages:
    for page in w.get_all_pages():
      pages.put(page)

  total_links = sum(len(links) for links in all_links)
  if verbose:
    print(f'Found a total of {total_links} total links')

  # Then, process the overall domains to see if they're dead or dangerous
  dead_domains = {}
  dangerous_domains = {}
  domains = list(all_domains)
  for i in range(0, len(domains), 500): # We can only request 500 domains at a time.
    domain_verifier(domains[i:i+500], dead_domains, dangerous_domains)

  if verbose:
    print(f'Found a total of {len(dead_domains)} dead domains and {len(dangerous_domains)} dangerous domains')

  # If we found any domains that are dead, replicate that discovery to any links on the same domain
  dead_links = {}
  for domain, reason in dead_domains.items():
    for link in all_links[domain]:
      dead_links[link] = reason
    del all_links[domain]

  # If we found any domains that are dangerous, replicate that discovery to any links on the same domain
  dangerous_links = {}
  for domain, reason in dangerous_domains.items():
    for link in all_links[domain]:
      dangerous_links[link] = reason
    del all_links[domain]

  if verbose:
    print('Starting linkscrapers')

  # We give each scraper a single domain's links, so that we can avoid getting throttled too hard.
  # Start with the domains that have the most links
  sorted_domains = list(all_links.keys())
  sorted_domains.sort(key=lambda domain: len(all_links[domain]), reverse=True)

  # Finally, process the remaining links to check for individual page 404s, redirects, etc.
  with pagescraper_queue(link_verifier, dead_links) as links:
    for domain in sorted_domains:
      links.put(all_links[domain])

  if verbose:
    print(f'Finished linkscrapers, found {len(dead_links)} total dead pages')

  output = """\
{{{{DISPLAYTITLE: {bad_links} broken or dangerous external links}}}}
<onlyinclude>{bad_links}</onlyinclude> out of {total_links} external links go to broken or dangerous-looking webpages across {bad_domains} domains. Data as of {date}.

{{{{TOC limit|3}}}}
""".format(
    bad_links=len(dead_links) + len(dangerous_links),
    total_links=total_links,
    bad_domains=len(dead_domains) + len(dangerous_domains),
    date=time_and_date())

  # Avoid rendering images inline
  def link_escape(link):
    if (
      'tinyurl' in link or
      link.endswith('.png') or
      link.endswith('.jpg')
    ):
      return link.replace('/', '&#47;')
    return link

  if len(dangerous_links) > 0:
    output += '= Dangerous links =\n'
    for dangerous_link in sorted(dangerous_links.keys(), key=lambda link:dangerous_links[link]):
      output += f'== {link_escape(dangerous_link)}: {dangerous_links[dangerous_link]} ==\n'
      for page in sorted(page_links.keys()):
        if dangerous_link in page_links[page]:
          output += f'* [[{page.title}]]\n'

  if len(dead_links) > 0:
    output += '= Broken links =\n'

    # Alphabetize the hostnames
    def sort_key(domain):
      domain = domain.replace('://www.', '://')
      domain = domain.replace('https://', '')
      domain = domain.replace('http://', '')
      return domain
    sorted_domains.sort(key=sort_key)

    for domain in sorted_domains:
      dead_domain_links = [link for link in all_links[domain] if link in dead_links]
      if len(dead_domain_links) > 0:
        output += f'== {domain} ({len(dead_domain_links)}) ==\n'
        for link in sorted(dead_domain_links):
          output += f'=== {link_escape(link)}: {dead_links[link]} ===\n'
          for page in sorted(page_links.keys()):
            if link in page_links[page]:
              output += f'* [[{page.title}]]\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_external_links.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

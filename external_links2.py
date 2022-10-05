from os import environ
from re import compile, VERBOSE
from time import sleep
from utils import pagescraper_queue, time_and_date
from wikitools import wiki
import requests

verbose = True

# Within the HTML source code, all links should be href="()". Internal links start with /wiki/foo, so this find all external links.
LINK_REGEX = compile('''
  href="(       # Within the HTML source code, all links start with href=
    (           # Start inner capture group (for just the domain name)
      https?:// # Match http/https scheme (internal wiki links start with /wiki)
      [^/"]+    # The domain
    )
    [^"]*       # The rest of the URL
  )"
''', VERBOSE)

def pagescraper(page, page_links, all_domains, all_links):
  if verbose:
    print(f'Processing {page.title}')

  text = page.get_raw_html()

  links = set()
  for m in LINK_REGEX.finditer(text):
    domain = m.group(2)
    if domain == 'https://wiki.teamfortress.com':
      continue # We don't need to worry about direct links into the wiki (which often come from {{Navbar float}})
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
    r = requests.request(verb, url, timeout=timeout)
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
  print('safebrowsing response:\n', r.text)
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
  if verbose:
    print(f'Done with domain {list(links)[0]}: {len(links)}')

def main(w):
  # First, scrape all the links from all of the pages
  page_links = {} # Map of page: {links}
  all_domains = set()
  all_links = {} # Map of domain: {links}
  with pagescraper_queue(pagescraper, page_links, all_domains, all_links) as pages:
    for page in w.get_all_pages():
      pages.put(page)

  # For reporting purposes
  link_count = sum(len(links) for links in all_links)
  if verbose:
    print(f'Found a total of {link_count} links')

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
  domains = [(len(domain_links), domain_links) for domain_links in all_links.values()]
  domains.sort(reverse=True)
  for count, domain_links in domains:
    parts = domain_links[0].split('/')
    guess = '/'.join(domain_links[:3])
    print(f'{guess} {count}')
  exit()

  # Finally, process the remaining links to check for individual page 404s, redirects, etc.
  with pagescraper_queue(link_verifier, dead_links) as links:
    for _, domain_links in domains[:100]: # Limited domains because otherwise we take too long and time out
      links.put(domain_links)
    print('[main thread] All links put')

  if verbose:
    print('Generating report')

  page_count = 0
  for page, links in page_links.items():
    if any((link in dead_links) for link in links):
      page_count += 1
    elif any((link in dangerous_links) for link in links):
      page_count += 1

  if verbose:
    print(f'Finished linkscrapers, found {page_count} total bad pages')

  output = """\
{{{{DISPLAYTITLE: {page_count} pages with broken or dangerous external links}}}}
<onlyinclude>{page_count}</onlyinclude> pages have a broken or dangerous-looking external links. Processed {link_count} over {domain_count} domains. Data as of {date}.

{{{{TOC limit|2}}}}
""".format(
    page_count=page_count,
    link_count=link_count,
    domain_count=len(all_domains),
    date=time_and_date())

  # Working around the page blacklist, mebe
  def link_escape(link):
    do_escape = (
      'tinyurl' in link or
      link.endswith('.png') or
      link.endswith('.jpg')
    )

    return link.replace('/', '&#47;') if do_escape else link

  if len(dangerous_links) > 0:
    output += '= Dangerous links =\n'
    for dangerous_link in sorted(dangerous_links.keys(), key=lambda link:dangerous_links[link]):
      output += f'== {link_escape(dangerous_link)}: {dangerous_links[dangerous_link]} ==\n'
      for page in sorted(page_links.keys()):
        if dangerous_link in page_links[page]:
          output += f'* [[{page.title}]]\n'

  if len(dead_links) > 0:
    output += '= Broken links =\n'
    for dead_link in sorted(dead_links.keys(), key=lambda link:dead_links[link]):
      output += f'== {link_escape(dead_link)}: {dead_links[dead_link]} ==\n'
      for page in sorted(page_links.keys()):
        if dead_link in page_links[page]:
          output += f'* [[{page.title}]]\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_external_links.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

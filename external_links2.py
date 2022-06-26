from re import compile, VERBOSE
from utils import pagescraper_queue, pagescraper_queue_single, time_and_date
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

def safely_request(verb, url, timeout=20):
  try:
    r = requests.request(verb, url, timeout=timeout)
  except requests.exceptions.ConnectionError:
    return '404 NOT FOUND'
  except requests.exceptions.Timeout:
    return '504 GATEWAY TIMEOUT'
  except requests.exceptions.TooManyRedirects:
    return '508 LOOP DETECTED'

  if r.is_redirect:
    return '508 LOOP DETECTED'
  elif not r.ok:
    if verbose:
      print(f'Error while accessing {url}: {r.status_code}\n{r.text}')
    return f'{r.status_code} {r.reason.upper()}'
  return None # no error

def domain_verifier(domain, dead_domains, dangerous_domains):
  # TODO: https://developers.google.com/safe-browsing/v4/lookup-api
  if False:
    dangerous_domains[domain] = 'reason'

  if reason := safely_request('HEAD', domain, timeout=60):
    dead_domains[domain] = reason
    return

def link_verifier(link, dead_links):
  if reason := safely_request('GET', link):
    dead_links[link] = reason

def main(w):
  # First, scrape all the links from all of the pages
  page_links = {} # Map of page: {links}
  all_domains = set()
  all_links = {} # Map of domain: {links}
  with pagescraper_queue(pagescraper, page_links, all_domains, all_links) as pages:
    i = 0
    for page in w.get_all_pages():
      pages.put(page)
      i += 1
      if i >= 200:
        break

  # For reporting purposes
  link_count = sum(len(links) for links in all_links)
  if verbose:
    print(f'Found a total of {link_count} links')

  # Then, process the overall domains to see if they're dead or dangerous
  dead_domains = {}
  dangerous_domains = {}
  with pagescraper_queue_single(domain_verifier, dead_domains, dangerous_domains) as domains:
    for domain in all_domains:
      domains.put(domain)

  if verbose:
    print(f'Found a total of {len(dead_domains)} dead domains and {len(dangerous_domains)} dangerous domains')

  dead_links = {}
  # To avoid threading issues (although python should handle them fine), reprocess domains in the main thread.
  for domain, reason in dead_domains.items():
    for link in all_links[domain]:
      dead_links[link] = reason
    del all_links[domain]

  dangerous_links = {}
  for domain, reason in dangerous_domains.items():
    for link in all_links[domain]:
      dangerous_links[link] = reason
    del all_links[domain]

  if verbose:
    print('Starting linkscrapers')

  # Finally, process the remaining links to check for individual page 404s, redirects, etc.
  with pagescraper_queue_single(link_verifier, dead_links) as links:
    for domain_links in all_links.values():
      for link in domain_links:
        links.put(link)

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
__NOFOLLOW__ <!-- We do not want to improve these links' SEO, so don't follow links on this page. -->
<onlyinclude>{page_count}</onlyinclude> pages have a broken or dangerous-looking external links. Processed {link_count} over {domain_count} domains. Data as of {date}.

{{{{TOC limit|2}}}}
""".format(
    page_count=page_count,
    link_count=link_count,
    domain_count=len(all_domains),
    date=time_and_date())

  # Working around the page blacklist, mebe
  def link_escape(link):
    return link #.replace('/', '&#47;')

  if len(dangerous_links) > 0:
    output += '= Dangerous links =\n'
    for link in sorted(dangerous_links.keys(), key=lambda link:dangerous_links[link]):
      output += f'== {link_escape(link)}: {dangerous_links[link]} ==\n'
      for page, links in page_links.items():
        if link in links:
          output += f'* [{page.get_edit_url()} {page.title}]\n'

  if len(dead_links) > 0:
    output += '= Broken links =\n'
    for link in sorted(dead_links.keys(), key=lambda link:dead_links[link]):
      output += f'== {link_escape(link)}: {dead_links[link]} ==\n'
      for page, links in page_links.items():
        if link in links:
          output += f'* [{page.get_edit_url()} {page.title}]\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_external_links.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

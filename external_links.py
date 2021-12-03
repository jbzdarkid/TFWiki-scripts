from json import loads
from queue import Queue, Empty
from re import compile, DOTALL
from threading import Thread, Event
import requests
from time import sleep
from wikitools import wiki
from wikitools.page import Page

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']
PAGESCRAPERS = 10
LINKCHECKERS = 50

# Shamelessly copied from the old external_links_analyse.
def return_link_regex(withoutBracketed=False, onlyBracketed=False):
  """Return a regex that matches external links."""
  # RFC 2396 says that URLs may only contain certain characters.
  # For this regex we also accept non-allowed characters, so that the bot
  # will later show these links as broken ('Non-ASCII Characters in URL').
  # Note: While allowing dots inside URLs, MediaWiki will regard
  # dots at the end of the URL as not part of that URL.
  # The same applies to comma, colon and some other characters.
  notAtEnd = '\]\s\.:;,<>"\|)'
  # So characters inside the URL can be anything except whitespace,
  # closing squared brackets, quotation marks, greater than and less
  # than, and the last character also can't be parenthesis or another
  # character disallowed by MediaWiki.
  notInside = '\]\s<>"'
  # The first half of this regular expression is required because '' is
  # not allowed inside links. For example, in this wiki text:
  #   ''Please see http://www.example.org.''
  # .'' shouldn't be considered as part of the link.
  regex = r'(?P<url>http[s]?://[^' + notInside + ']*?[^' + notAtEnd \
    + '](?=[' + notAtEnd+ ']*\'\')|http[s]?://[^' + notInside \
    + ']*[^' + notAtEnd + '])'

  if withoutBracketed:
    regex = r'(?<!\[)' + regex
  elif onlyBracketed:
    regex = r'\[' + regex
  return compile(regex)

# Also shamelessly copied from the old external_links_analyse.
def get_links(regex, text):
  nestedTemplateR = compile(r'{{([^}]*?){{(.*?)}}(.*?)}}')
  while nestedTemplateR.search(text):
    text = nestedTemplateR.sub(r'{{\1 \2 \3}}', text)

  # Then blow up the templates with spaces so that the | and }} will not be regarded as part of the link:.
  templateWithParamsR = compile(r'{{([^}]*?[^ ])\|([^ ][^}]*?)}}', DOTALL)
  while templateWithParamsR.search(text):
    text = templateWithParamsR.sub(r'{{ \1 | \2 }}', text)

  for m in regex.finditer(text):
    yield m.group('url')

# End of stuff I shamelessly copied.

def pagescraper(page_q, done, link_q, links):
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  while True:
    try:
      page = page_q.get(True, 1)['title']
    except Empty:
      if done.is_set():
        return
      else:
        continue

    content = Page(w, page).get_wiki_text()
    linkRegex = return_link_regex()
    for url in get_links(linkRegex, content):
      if url not in links:
        links[url] = []
        link_q.put(url)
      if page not in links[url]:
        links[url].append(page)

def linkchecker(link_q, done, linkData):
  while True:
    try:
      link = link_q.get(True, 1)
    except Empty:
      if done.is_set():
        return
      else:
        continue

    try:
      r = requests.get(link, timeout=20)
      r.raise_for_status()
      continue # No error
    except requests.exceptions.ConnectionError:
      linkData.append(('Not found', link))
    except requests.exceptions.Timeout:
      linkData.append(('Timeout', link))
    except requests.exceptions.TooManyRedirects:
      linkData.append(('Redirect loop', link))
    except requests.exceptions.HTTPError as e:
      code = e.response.status_code
      if code == 301 or code == 302 or code == 303:
        linkData.append(('Redirect Loop', link))
      else:
        linkData.append((e.response.reason, link))

    if verbose:
      print(f'Found an error for {link}')

def main():
  threads = []
  # Stage 0: Generate list of pages
  if verbose:
    print('Generating page list')
  page_q, done = Queue(), Event()
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  for page in w.get_all_pages():
    if page['title'].rpartition('/')[2] in LANGS:
      continue # Filter out non-english pages
    page_q.put(page)
  done.set()
  if verbose:
    print('All pages generated, entering stage 1')
  # Stage 1: All pages generated. Pagescrapers are allowed to exit if Page Queue is empty.
  links = {}
  link_q = Queue()
  for i in range(PAGESCRAPERS): # Number of threads
    thread = Thread(target=pagescraper, args=(page_q, done, link_q, links))
    threads.append(thread)
    thread.start()
  if verbose:
    print('All pages scraped, entering stage 2')
  # Stage 2: All pages scraped. Linkscrapers are allowed to exit if Link Queue is empty.
  _linkData = []
  for i in range(LINKCHECKERS): # Number of threads
    thread = Thread(target=linkchecker, args=(link_q, done, _linkData))
    threads.append(thread)
    thread.start()
  if verbose:
    print('Waiting for linkscrapers to finish')
  for thread in threads:
    thread.join()

  if verbose:
    print('Done scraping links, generating output')

  output = '== Dead or incorrectly behaving links ==\n'
  linkData = sorted(_linkData)
  for error, link in linkData:
    output += '* %s (%s)\n' % (link, error)
    for page in sorted(links[link]):
      output += '** [[%s]]\n' % page
  output += '== Suspicious links ==\n'
  for link in links:
    suspicious = False
    for domain in ['wiki.tf2.com', 'wiki.teamfortress.com', 'wiki.tf', 'pastie', 'paste']:
      if domain in link:
        suspicious = True
        break
    if suspicious:
      output += '* %s\n' % link
    for page in sorted(links[link]):
      output += '** [[%s]]\n' % page

  output = output.replace('tumblr', 'tumb1r') # Link blacklist
  output = output.replace('amazon', 'amaz0n') # Link blacklist
  return output

if __name__ == '__main__':
  verbose = True
  f = open('wiki_external_links.txt', 'w')
  f.write(main())
  print('Article written to wiki_external_links.txt')
  f.close()

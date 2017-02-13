from urllib2 import quote
from Queue import Empty
from threading import Thread
from wikitools import wiki
from wikitools.page import Page
from re import search, sub
import utilities

verbose = False
PAGESCRAPERS = 10

def pagescraper(page_q, done, badpages):
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  while True:
    try:
      page = page_q.get(True, 1)['title']
    except Empty:
      if done.is_set(): # Pages are done being generated
        return
      else:
        continue

    page_text = Page(w, page).getWikiText()
    page_visible = sub('<includeonly>.*?</includeonly>', '', page_text)
    if float(len(page_visible)) / len(page_text) > .8:
      continue # Pages that show >8% of their information, e.g. nav templates
    else:
      if verbose:
        print page, 'shows', float(len(page_visible)) / len(page_text) * 100, '%'

    match = search('{{([Dd]oc begin|[Tt]emplate doc|[Dd]ocumentation|[Ww]ikipedia doc|[dD]ictionary/wrapper)}}', page_text)
    if not match:
      count = utilities.whatlinkshere(page)
      if verbose:
        print 'Page %s does not transclude a documentation template and has %d backlinks' % (page, count)
      badpages.append([count, page])

def main():
  page_q, done = utilities.get_list('templates')
  badpages = []
  threads = []
  for i in range(PAGESCRAPERS): # Number of threads
    thread = Thread(target=pagescraper, args=(page_q, done, badpages))
    threads.append(thread)
    thread.start()
  for thread in threads:
    thread.join()

  badpages.sort(key=lambda s: (-s[0], s[1]))
  output = '{{DISPLAYTITLE:%d templates without documentation}}\n' % len(badpages)
  for page in badpages:
    output += '* [[%s|]] ([{{fullurl:Special:WhatLinksHere/%s|limit=%d}} %d use%s])\n' % (page[1], page[1], page[0], page[0], '' if page[0] == 1 else 's')
  return output.encode('utf-8')

if __name__ == '__main__':
  verbose = True
  f = open('wiki_undocumented_templates.txt', 'wb')
  f.write(main())
  print 'Article written to wiki_undocumented_templates.txt'
  f.close()
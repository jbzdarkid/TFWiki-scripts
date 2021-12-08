from queue import Queue, Empty
from re import search, sub
from threading import Thread, Event
from wikitools import wiki
from wikitools.page import Page

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

    page_text = Page(w, page).get_wiki_text()
    page_visible = sub('<includeonly>.*?</includeonly>', '', page_text)
    if len(page_text) == 0:
      continue # Empty templates (usually due to HTTP failures)
    elif float(len(page_visible)) / len(page_text) > .80:
      continue # Pages that show >80% of their information, e.g. nav templates

    if verbose:
      print(page, 'shows', float(len(page_visible)) / len(page_text) * 100, '%')

    match = search('{{([Dd]oc begin|[Tt]emplate doc|[Dd]ocumentation|[Ww]ikipedia doc|[dD]ictionary/wrapper)}}', page_text)
    if not match:
      count = Page(w, page).get_transclusion_count()
      if verbose:
        print('Page %s does not transclude a documentation template and has %d backlinks' % (page, count))
      badpages.append([count, page])

def main():
  page_q, done = Queue(), Event()
  badpages = []
  threads = []
  for _ in range(PAGESCRAPERS): # Number of threads
    thread = Thread(target=pagescraper, args=(page_q, done, badpages))
    threads.append(thread)
    thread.start()

  try:
    w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
    for page in w.get_all_templates():
      if '/' in page['title']: # FIXME: Necessary?
        continue # Don't include subpages
      elif page['title'].partition('/')[0] == 'Template:Dictionary':
        continue # Don't include dictionary subpages
      elif page['title'].partition('/')[0] == 'Template:PatchDiff':
        continue # Don't include patch diffs.
      elif page['title'][:13] == 'Template:User':
        continue # Don't include userboxes.
      page_q.put(page)

  finally:
    done.set()
    for thread in threads:
      thread.join()

  badpages.sort(key=lambda s: (-s[0], s[1]))
  output = '{{DISPLAYTITLE:%d templates without documentation}}\n' % len(badpages)
  for count, title in badpages:
    output += '* [[%s|]] ([{{fullurl:Special:WhatLinksHere/%s|limit=%d|namespace=0|hideredirs=1|hidelinks=1}} %d use%s])\n' % (title, title, count, count, '' if count == 1 else 's')
  return output

if __name__ == '__main__':
  verbose = True
  f = open('wiki_undocumented_templates.txt', 'w')
  f.write(main())
  print('Article written to wiki_undocumented_templates.txt')
  f.close()

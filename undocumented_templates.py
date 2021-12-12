from queue import Queue, Empty
from re import search, sub
from threading import Thread, Event
from wikitools import wiki
from wikitools.page import Page

verbose = False
PAGESCRAPERS = 10

def pagescraper(w, page_q, done, badpages):
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
      continue # Template is self-documenting, as it shows the majority of its contents.
    elif '{{tlx|' in page_visible or '{{tl|' in page_visible:
      continue # Page has example usages
    elif search('{{([Dd]oc begin|[Tt]emplate doc|[Dd]ocumentation|[Ww]ikipedia doc|[dD]ictionary/wrapper)}}', page_visible):
      continue # Page uses a documentation template

    count = Page(w, page).get_transclusion_count()
    if verbose:
      print(f'Page {page} does not transclude a documentation template and has {count} backlinks')
    badpages.append([count, page])

def main(w):
  page_q, done = Queue(), Event()
  badpages = []
  threads = []
  for _ in range(PAGESCRAPERS): # Number of threads
    thread = Thread(target=pagescraper, args=(w, page_q, done, badpages))
    threads.append(thread)
    thread.start()

  try:
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
    output += '* [[%s|]] ([{{fullurl:Special:WhatLinksHere/%s|limit=%d&namespace=0&hideredirs=1&hidelinks=1}} %d use%s])\n' % (title, title, min(50, count), count, '' if count == 1 else 's')
  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_undocumented_templates.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

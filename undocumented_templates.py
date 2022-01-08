from queue import Queue, Empty
from re import search, sub
from threading import Thread, Event
from time import gmtime, strftime
from wikitools import wiki
from wikitools.page import Page

verbose = False
PAGESCRAPERS = 10

def pagescraper(w, page_q, done, badpages):
  while True:
    try:
      page = page_q.get(True, 1)
    except Empty:
      if done.is_set(): # Pages are done being generated
        return
      else:
        continue

    page_text = page.get_wiki_text()
    page_visible = sub('<includeonly>.*?</includeonly>', '', page_text)
    if len(page_text) == 0:
      continue # Empty templates (usually due to HTTP failures)
    elif float(len(page_visible)) / len(page_text) > .80:
      continue # Template is self-documenting, as it shows the majority of its contents.
    elif '{{tlx|' in page_visible or '{{tl|' in page_visible:
      continue # Page has example usages
    elif search('{{([Dd]oc begin|[Tt]emplate doc|[Dd]ocumentation|[Ww]ikipedia doc|[dD]ictionary/wrapper)}}', page_visible):
      continue # Page uses a documentation template

    count = page.get_transclusion_count()
    if count > 0:
      if verbose:
        print(f'Page {page.title} does not transclude a documentation template and has {count} backlinks')
      badpages.append([count, page.title])

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
      if '/' in page.title:
        continue # Don't include subpage templates like Template:Dictionary or Template:PatchDiff
      elif page.title[:13] == 'Template:User':
        continue # Don't include userboxes.
      page_q.put(page)

  finally:
    done.set()
    for thread in threads:
      thread.join()

  badpages.sort(key=lambda s: (-s[0], s[1]))
  output = """\
{{{{DISPLAYTITLE:{count} templates without documentation}}}}
There are <onlyinclude>{count}</onlyinclude> templates which are in use but are undocumented. Please either add a <nowiki><noinclude></nowiki> section with a usage guide, or make use of {{{{tl|Documentation}}}}. Data as of {date}.

""".format(
      count=len(badpages),
      date=strftime(r'%H:%M, %d %B %Y', gmtime()))

  for count, title in badpages:
    output += '* [[%s|]] ([{{fullurl:Special:WhatLinksHere/%s|limit=%d&namespace=0&hideredirs=1&hidelinks=1}} %d use%s])\n' % (title, title, min(50, count), count, '' if count == 1 else 's')
  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_undocumented_templates.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

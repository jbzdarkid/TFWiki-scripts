from wikitools import wiki
from datetime import datetime, timedelta

import displaytitles

# We are overwriting page_iter so that the weekly report can just process the past week of changes.
def page_iter(w):
  for page in w.get_recent_changes(datetime.utcnow() - timedelta(days=7), namespaces=['Main', 'TFW', 'File', 'Template', 'Help', 'Category']):
    yield page

displaytitles.page_iter = page_iter

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_displaytitles.txt', 'w', encoding='utf-8') as f:
    f.write(mismatched.main(w))
  print(f'Article written to {f.name}')


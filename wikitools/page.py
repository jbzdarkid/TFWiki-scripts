import functools
from requests.exceptions import RequestException
import requests
from time import sleep

@functools.total_ordering
class Page:
  def __init__(self, wiki, title, raw=None):
    self.wiki = wiki
    self.title = title
    self.url_title = title.replace(' ', '_')
    self.raw = raw

  def __str__(self):
    return self.title

  def __repr__(self):
    return f'Page(w, {self.title})'

  def __le__(self, other):
    return self.url_title < other.url_title

  def get_wiki_text(self):
    cached_text = self.wiki.page_text_cache.get(self.title, None)
    if cached_text:
      return cached_text
    try:
      text = self.wiki.get('parse', page=self.url_title, prop='wikitext')['parse']['wikitext']['*']
      self.wiki.page_text_cache[self.title] = text
      return text
    except RequestException:
      return '' # Unable to fetch page contents, pretend it's empty

  def get_raw_html(self):
    r = requests.get(self.wiki.wiki_url, allow_redirects=True, params={'title': self.url_title})
    return r.text

  def get_edit_url(self):
    return f'{self.wiki.wiki_url}?title={self.url_title}&action=edit'

  def get_transclusion_count(self):
    return sum(1 for _ in self.get_transclusions())

  # By default, only return links from the main namespace (ns:0)
  def get_transclusions(self, *, namespace=0):
    for entry in self.wiki.get_with_continue('query', 'embeddedin',
      list='embeddedin',
      einamespace=namespace,
      eilimit=500,
      eititle=self.url_title,
    ):
      yield Page(self.wiki, entry['title'], entry)

  def get_links(self):
    for entry in self.wiki.get_with_continue('query', 'pages',
      generator='links',
      gplnamespace=0, # Main
      gpllimit=500,
      titles=self.url_title,
    ):
      yield Page(self.wiki, entry['title'], entry)

  def get_file_link_count(self):
    # Unfortunately, the mediawiki APIs don't include file links, so we have to scrape the HTML.
    for html in self.wiki.get_html_with_continue('Special:WhatLinksHere', target=self.url_title, hidelinks=1, hidetrans=1, namespace=0):
      # Also, this report uses page IDs for iteration, so for now we're returning solely based on the first page of results.
      return html.count('mw-whatlinkshere-tools') # Class for (<-- links | edit)

  def edit(self, text, summary, bot=True):
    if len(text) > 3000 * 1000: # 3 KB
      text = '<span class="error">Warning: Report truncated to 3 KB</span>\n' + text[:3000 * 1000]

    # We would rather not lose all our hard work, so we try pretty hard to make the edit succeed.
    i = 0
    while True:
      try:
        data = self.wiki.post_with_csrf('edit',
          title=self.url_title,
          text=text,
          summary=summary,
          bot=bot,
        )
      except Exception as e:
        print(f'Attempt {i} failed:\n{e}')
        if i < 5:
          i += 1
          sleep(30)
        else:
          print(f'Failed to edit {self.title}:')
          print(e)
          return

    if 'error' in data:
      print(f'Failed to edit {self.title}:')
      print(data['error'])
    elif data['edit']['result'] != 'Success':
      print(f'Failed to edit {self.title}:')
      print(data['edit'])
    elif 'new' in data['edit']:
      print(f'Successfully created {self.title}.')
      return 'https://wiki.tf/d/' + str(data['edit']['newrevid'])
    elif 'nochange' in data['edit']:
      print(f'No change to {self.title}')
    else:
      print(f'Successfully edited {self.title}')
      return 'https://wiki.tf/d/' + str(data['edit']['newrevid'])

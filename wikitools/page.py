import functools
from requests.exceptions import RequestException
import requests

@functools.total_ordering
class Page:
  def __init__(self, wiki, title, raw=None):
    self.wiki = wiki
    self.title = title
    self.url_title = title.replace(' ', '_')
    self.raw = raw

  def __str__(self):
    return self.title

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

  # Do not use this. Just iterate all pages instead.
  # def exists(self):
  #   r = requests.head(self.wiki.wiki_url, allow_redirects=True, params={'title': self.url_title})
  #   return r.status_code == 200

  def get_edit_url(self):
    return f'{self.wiki.wiki_url}?title={self.url_title}&action=edit'

  # TODO: Deprecate
  def get_transclusion_count(self):
    return sum(1 for _ in self.get_transclusions())

  def get_transclusions(self):
    return [Page(self.wiki, entry['title'], entry) for entry in self.wiki.get_with_continue('query', 'embeddedin',
      list='embeddedin',
      eifilterredir='nonredirects', # Filter out redirects
      einamespace=0, # Links from the Main namespace only
      eilimit=500,
      eititle=self.url_title,
    )]

  # This should probably be on page.py though
  def get_links(self):
    return [Page(self.wiki, entry['title'], entry) for entry in self.wiki.get_with_continue('query', 'pages',
      generator='links',
      gplnamespace=0, # Main
      gpllimit=500,
      titles=self.url_title,
    )]

  # TODO: Rename, ambiguous (file links only)
  def get_link_count(self):
    # All links, from the main namespace only
    # Unfortunately, the mediawiki APIs don't include file links, which is the main reason I use this right now.
    html = next(self.wiki.get_html_with_continue('Special:WhatLinksHere', target=self.url_title, namespace=0))
    # This report uses page IDs for iteration which is just unfortunate.
    return html.count('mw-whatlinkshere-tools') # Class for (<-- links | edit)

  def edit(self, text, summary, bot=True):
    if len(text) > 4000 * 1000: # 4 KB
      text = text[:4000 * 1000]
      print('Warning: Truncated text to 4 KB (max page length)')

    data = self.wiki.post_with_csrf('edit',
      title=self.url_title,
      text=text,
      summary=summary,
      bot=bot,
    )
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

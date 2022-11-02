from requests.exceptions import RequestException
from time import sleep
import functools
import requests

@functools.total_ordering
class Page:
  def __init__(self, wiki, title, raw=None):
    self.wiki = wiki
    self.title = title
    self.url_title = title.replace(' ', '_')
    self.raw = raw

    self.basename, _, self.lang = title.rpartition('/')
    if self.lang not in 'ar cs da de es fi fr hu it ja ko nl no pl pt pt-br ro ru sv tr zh-hans zh-hant'.split(' '):
      self.basename = title
      self.lang = 'en'

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
      raw = self.wiki.get('parse', page=self.url_title, prop='wikitext')
      if 'error' in raw:
        print(f'Error while fetching {self.url_title} contents: ' + str(raw['error']))
        return '' # Unable to fetch page contents, pretend it's empty
      text = raw['parse']['wikitext']['*']
      self.wiki.page_text_cache[self.title] = text
      return text
    except RequestException:
      return '' # Unable to fetch page contents, pretend it's empty

  def get_raw_html(self):
    cached_html = self.wiki.page_html_cache.get(self.title, None)
    if cached_html:
      return cached_html
    try:
      r = requests.get(self.wiki.wiki_url, allow_redirects=True, params={'title': self.url_title})
      self.wiki.page_html_cache[self.title] = r.text
      return r.text
    except RequestException:
      return '' # Unable to fetch page contents, pretend it's empty

  def get_page_url(self, **kwargs):
    params = ''.join([f'&{key}={value}' for key, value in kwargs.items()])
    url = f'{self.wiki.wiki_url}?title={self.url_title}{params}'
    url = url.replace(' ', '%20')
    return url

  def get_edit_url(self):
    return self.get_page_url(action='edit')

  def get_transclusion_count(self):
    return sum(1 for _ in self.get_transclusions())

  def get_transclusions(self, *, namespace='Main'):
    for entry in self.wiki.get_with_continue('query', 'embeddedin',
      list='embeddedin',
      einamespace=self.wiki.namespaces[namespace],
      eilimit=500,
      eititle=self.url_title,
    ):
      yield Page(self.wiki, entry['title'], entry)

  def get_links(self, *, namespace='Main'):
    for entry in self.wiki.get_with_continue('query', 'pages',
      generator='links',
      gplnamespace=self.wiki.namespaces[namespace],
      gpllimit=500,
      titles=self.url_title,
    ):
      yield Page(self.wiki, entry['title'], entry)

  def get_file_link_count(self):
    # Unfortunately, the mediawiki APIs don't include file links, so we have to scrape the HTML.
    for html in self.wiki.get_html_with_continue('Special:WhatLinksHere',
      target=self.url_title,
      hidelinks=1,
      hidetrans=1,
      namespace=self.wiki.namespaces['Main'],
    ):
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
        break
      except Exception as e:
        print(f'Attempt {i} failed:\n{e}')
        if i < 5:
          i += 1
          sleep(30)
        else:
          print(f'Failed to edit {self.title}:\n{e}')
          return None

    if 'error' in data:
      print(f'Failed to edit {self.title}:')
      print(data['error'])
      return None
    elif data['edit']['result'] != 'Success':
      print(f'Failed to edit {self.title}:')
      print(data['edit'])
      return None
    elif 'new' in data['edit']:
      print(f'Successfully created {self.title}')
      return self.wiki.wiki_url + '?diff=' + str(data['edit']['newrevid'])
    elif 'nochange' in data['edit']:
      print(f'No change to {self.title}')
      return None
    else:
      print(f'Successfully edited {self.title}')
      return self.wiki.wiki_url + '?diff=' + str(data['edit']['newrevid'])

  def upload(self, fileobj, comment=''):
    if fileobj.mode != 'rb':
      print(f'Failed to upload {self.title}, file must be opened in rb (was {fileobj.mode})')
      return
    print(f'Uploading {self.title}...')
    data = self.wiki.post_with_csrf('upload',
      filename=self.url_title,
      file=fileobj.name,
      comment=comment,
      files={'file': (fileobj.name, fileobj, 'multipart/form-data')},
      ignorewarnings=True,
    )

    if 'error' in data:
      print(f'Failed to upload {self.title}:')
      print(data['error'])
    elif data['upload']['result'] != 'Success':
      print(f'Failed to upload {self.title}:')
      print(data['upload'])
    else:
      print('Successfully uploaded ' + data['upload']['filename'])

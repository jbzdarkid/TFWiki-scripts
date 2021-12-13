from requests.exceptions import RequestException

class Page:
  def __init__(self, wiki, title, raw=None):
    self.wiki = wiki
    self.title = title.replace(' ', '_')
    self.raw = raw

  def __str__(self):
    return self.title

  def get_wiki_text(self):
    try:
      return self.wiki.get('parse', page=self.title, prop='wikitext')['parse']['wikitext']['*']
    except RequestException:
      return '' # Unable to fetch page contents, pretend it's empty

  # Do not use this. Just iterate all pages instead.
  # def exists(self):
  #   r = requests.head(self.wiki.wiki_url, allow_redirects=True, params={'title': self.title})
  #   return r.status_code == 200

  def get_edit_url(self):
    return f'{self.wiki.wiki_url}?title={self.title}&action=edit'

  # TODO: Deprecate
  def get_transclusion_count(self):
    return sum(1 for _ in self.get_transclusions())

  def get_transclusions(self):
    return self.wiki.get_with_continue('query', 'embeddedin',
      list='embeddedin',
      eifilterredir='nonredirects', # Filter out redirects
      einamespace=0, # Links from the Main namespace only
      eilimit=500,
      eititle=self.title,
    )

  # This should probably be on page.py though
  def get_links(self):
    return self.wiki.get_with_continue('query', 'pages',
      generator='links',
      gplnamespace=0, # Main
      gpllimit=500,
      titles=self.title,
    )

  # TODO: Rename, ambiguous
  def get_link_count(self):
    # All links, from the main namespace only
    # Unfortunately, the mediawiki APIs don't include file links, which is the main reason I use this right now.
    html = next(self.wiki.get_html_with_continue('Special:WhatLinksHere', target=self.title, namespace=0))
    # This report uses page IDs for iteration which is just unfortunate.
    return html.count('mw-whatlinkshere-tools') # Class for (<-- links | edit)

  def edit(self, text, summary, bot=True):
    data = self.wiki.post_with_csrf('edit',
      title=self.title,
      text=text,
      summary=summary,
      bot=bot,
    )
    if data['edit']['result'] != 'Success':
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

import requests

class Page:
  def __init__(self, wiki, title):
    self.wiki = wiki
    self.title = title.replace(' ', '_')

  def __str__(self):
    return self.title

  def get_wiki_text(self):
    return self.wiki.get('parse', page=self.title, prop='wikitext')['parse']['wikitext']['*']

  def exists(self):
    raise # Do not use this. Just iterate all pages instead.
    r = requests.head(self.wiki.wiki_url, allow_redirects=True, params={'title': self.title})
    return r.status_code == 200

  def get_edit_url(self):
    return f'{self.wiki.wiki_url}?title={self.title}&action=edit'

  def get_transclusion_count(self):
    transclusions = self.wiki.get_with_continue('query', 'embeddedin',
      list='embeddedin',
      eifilterredir='nonredirects', # Filter out redirects
      einamespace='0', # Links from the Main namespace only
      eilimit='500',
      eititle=self.title,
    )
    return sum(1 for _ in transclusions)

  def get_link_count(self):
    links = self.wiki.get_with_continue('query', 'pages',
      generator='linkshere',
      glhshow='!redirect', # Filter out redirects
      glhnamespace='0', # Links from the Main namespace only
      glhlimit='500',
      titles=self.title,
    )
    return sum(1 for _ in links)

  def edit(self, text, summary, bot=True):
    data = self.wiki.post_with_login('edit',
      title=self.title,
      text=text,
      summary=summary,
      bot=bot,
      token=self.wiki.get_csrf_token(),
    )
    if data['edit']['result'] != 'Success':
      return f'Failed to edit {self.title}:\n' + data['edit']
    elif 'new' in data['edit']:
      return 'Successfully created page ' + data['edit']['title']
    elif 'nochange' in data['edit']:
      return 'No change to ' + data['edit']['title']
    else:
      return 'Successfully edited ' + data['edit']['title']

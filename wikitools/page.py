from requests.exceptions import RequestException

class Page:
  def __init__(self, wiki, title):
    self.wiki = wiki
    self.title = title.replace(' ', '_')

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

  def get_transclusion_count(self):
    try:
      transclusions = self.wiki.get_with_continue('query', 'embeddedin',
        list='embeddedin',
        eifilterredir='nonredirects', # Filter out redirects
        einamespace='0', # Links from the Main namespace only
        eilimit='500',
        eititle=self.title,
      )
      return sum(1 for _ in transclusions)
    except RequestException:
      return 0

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
      return f'Failed to edit {self.title}:\n' + data['edit']
    elif 'new' in data['edit']:
      return 'Successfully created page ' + data['edit']['title']
    elif 'nochange' in data['edit']:
      return 'No change to ' + data['edit']['title']
    else:
      return 'Successfully edited ' + data['edit']['title']

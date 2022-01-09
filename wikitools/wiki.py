from re import finditer
from requests.exceptions import RequestException
from time import sleep
import requests

from .page import Page

# List of namespaces: https://wiki.teamfortress.com/w/api.php?action=query&meta=siteinfo&siprop=namespaces

class Wiki:
  def __init__(self, api_url):
    self.api_url = api_url
    self.wiki_url = api_url.replace('api.php', 'index.php')
    self.lgtoken = None
    self.page_text_cache = {}

    # As of MediaWiki 1.27, logging in and remaining logged in requires correct HTTP cookie handling by your client on all requests.
    self.session = requests.Session()

  def get(self, action, **params):
    params.update({
      'action': action,
      'format': 'json',
    })
    r = self.session.get(self.api_url, params=params)
    r.raise_for_status()
    j = r.json()
    if 'warnings' in j:
      print(r.url + '\tWarning: ' + j['warnings']['main']['*'])
    return j

  def get_with_continue(self, action, entry_key, **kwargs):
    while 1:
      try:
        data = self.get(action, **kwargs)
      except RequestException:
        return # Unable to load more info for this query
      if data == {'batchcomplete': ''}:
        return # No entries for this query
      if 'error' in data:
        print('Error: ' + str(data['error']))
        break

      try:
        entries = data[action][entry_key]
      except KeyError:
        if action not in data:
          print(f'Entry key "{entry_key}" was not found in data. Did you mean one of these keys: {", ".join(data.keys())}')
        else:
          print(f'Entry key "{entry_key}" was not found in data[{action}]. Did you mean one of these keys: {", ".join(data[action].keys())}')
        break

      if isinstance(entries, list):
        for entry in entries:
          yield entry
      elif isinstance(entries, dict):
        for entry in entries.values():
          yield entry

      if 'continue' in data:
        kwargs.update(data['continue'])
      else:
        break

  def get_html_with_continue(self, title, **params):
    params.update({
      'title': title,
      'limit': 500,
      'offset': 0,
    })
    while True:
      r = self.session.get(self.wiki_url, params=params)
      if not r.ok:
        yield '' # Not sure this is the best approach, but some reports return a 404 when there is no more data
        return
      if 'There are no results for this report.' in r.text:
        return

      yield r.text
      params['offset'] += params['limit']

  def post_with_login(self, action, **kwargs):
    if not self.lgtoken:
      raise ValueError('Error: Not logged in')
    kwargs.update({
      'lgtoken': self.lgtoken,
      'action': action,
      'format': 'json',
    })
    r = self.session.post(self.api_url, data=kwargs)
    try:
      return r.json()
    except:
      print(r.status_code, r.text)
      raise

  def post_with_csrf(self, action, **kwargs):
    # We would rather not lose all our hard work, so we try pretty hard to make the edit succeed.
    i = 0
    while True:
      try:
        kwargs['token'] = self.get('query', meta='tokens')['query']['tokens']['csrftoken']
        return self.post_with_login(action, **kwargs)
      except e:
        print(f'Attempt {i} failed:\n{e}')
        if i < 5:
          i += 1
          sleep(4**i)
        else:
          raise

  def get_all_templates(self):
    for entry in self.get_with_continue('query', 'allpages',
      list='allpages',
      aplimit=500,
      apfilterredir='nonredirects', # Filter out redirects
      apnamespace='10', # Template namespace
    ):
      yield Page(self, entry['title'], entry)

  def get_all_users(self):
    return self.get_with_continue('query', 'allusers',
      list='allusers',
      aulimit=500,
      auprop='editcount|registration',
      auwitheditsonly='true',
    )

  def get_all_pages(self):
    # TODO: Wait, does allpages have a namespace restriction? hmmm....
    for entry in self.get_with_continue('query', 'allpages',
      list='allpages',
      aplimit=500,
      apfilterredir='nonredirects', # Filter out redirects
    ):
      title = entry['title']
      if title.endswith('.js') or title.endswith('.css'):
        continue
      yield Page(self, title, entry)

  def get_all_categories(self, filter_redirects=True):
    for entry in self.get_with_continue('query', 'allpages',
      list='allpages',
      aplimit=500,
      apnamespace=14, # Categories
      apfilterredir='nonredirects' if filter_redirects else None,
    ):
      yield Page(self, entry['title'], entry)

  def get_all_category_pages(self, category):
    for entry in self.get_with_continue('query', 'categorymembers',
      list='categorymembers',
      cmlimit=500,
      cmtitle=category,
      cmprop='title', # Only return page titles, not page IDs
      cmnamespace='0', # Links from the Main namespace only
    ):
      yield Page(self, entry['title'], entry)

  def get_all_files(self):
    for entry in self.get_with_continue('query', 'pages',
      generator='allimages',
      gailimit=500,
      prop='duplicatefiles', # Include info about duplicates
    ):
      yield Page(self, entry['title'], entry)

  def get_all_unused_files(self):
    for html in self.get_html_with_continue('Special:UnusedFiles'):
      for m in finditer('<img alt="(.*?)"', html):
        yield m.group(1)

  def get_all_wanted_templates(self):
    for html in self.get_html_with_continue('Special:WantedTemplates'):
      for m in finditer('<a .*? class="new" .*?>(.*?)</a>', html):
        yield m.group(1)

  def login(self, username, password=None):
    print(f'Logging in as {username}...')
    self.lgtoken = self.get('query',
      meta='tokens',
      type='login',
    )['query']['tokens']['logintoken']

    if not password:
      import getpass
      password = getpass.getpass(f'Wiki password for {username}: ')

    data = self.post_with_login('login',
      lgname=username,
      lgpassword=password,
    )

    if data['login']['result'] == 'NeedToken':
      self.lgtoken = data['login']['token']
      data = self.post_with_login('login',
        lgname=username,
        lgpassword=password,
      )

    if data['login']['result'] != 'Success':
      print('Login failed: ' + data['login']['reason'])
      return False

    print(f'Successfully logged in as {username}')
    return True

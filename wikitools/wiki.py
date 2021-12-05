from requests.exceptions import RequestException
from time import sleep
import requests

# List of namespaces: https://wiki.teamfortress.com/w/api.php?action=query&meta=siteinfo&siprop=namespaces

class Wiki:
  def __init__(self, api_url):
    self.api_url = api_url
    self.wiki_url = api_url.replace('api.php', 'index.php')
    self.lgtoken = None

    # As of MediaWiki 1.27, logging in and remaining logged in requires correct HTTP cookie handling by your client on all requests.
    self.session = requests.Session()

  def get(self, action, **kwargs):
    kwargs.update({
      'action': action,
      'format': 'json',
    })
    r = self.session.get(self.api_url, params=kwargs)
    r.raise_for_status()
    return r.json()

  def get_with_continue(self, action, entry_key, **kwargs):
    while 1:
      try:
        data = self.get(action, **kwargs)
      except RequestException:
        return # Unable to load more info for this query
      if data == {'batchcomplete': ''}:
        return # No entries for this query
      try:
        entries = data[action][entry_key]
      except KeyError:
        print(f'Entry key "{entry_key}" was not found in data. Did you mean one of these keys: {data[action].keys()}')
        break

      if 'list' in kwargs:
        for entry in entries:
          yield entry
      elif 'generator' in kwargs:
        for value in entries.values():
          yield value

      if 'continue' in data:
        kwargs.update(data['continue'])
      else:
        break

  def post_with_login(self, action, **kwargs):
    if not self.lgtoken:
      raise ValueError('Error: Not logged in')
    kwargs.update({
      'lgtoken': self.lgtoken,
      'action': action,
      'format': 'json',
    })
    r = self.session.post(self.api_url, data=kwargs)
    return r.json()

  def post_with_csrf(self, action, **kwargs):
    # We absolutely need a CSRF token to make a POST request here, and we would rather not lose all our hard work.
    # So, we try 5 times and disregard all errors
    i = 0
    while True:
      try:
        kwargs['csrf_token'] = self.get('query', meta='tokens')['query']['tokens']['csrftoken']
        return self.post_with_login(action, **kwargs)
      except RequestException:
        if i < 5:
          i += 1
          sleep(4**i)
        else:
          raise

  def get_all_templates(self):
    return self.get_with_continue('query', 'allpages',
      list='allpages',
      aplimit='500',
      apfilterredir='nonredirects', # Filter out redirects
      apnamespace='10',
    )

  def get_all_users(self):
    return self.get_with_continue('query', 'allusers',
      list='allusers',
      aulimit='500',
      auprop='editcount|registration',
      auwitheditsonly='true',
    )

  def get_all_bots(self):
    return self.get_with_continue('query', 'allusers',
      list='allusers',
      aulimit='500',
      aurights='bot', # Only return bots
    )

  def get_all_pages(self):
    return self.get_with_continue('query', 'allpages',
      list='allpages',
      aplimit='500',
      apfilterredir='nonredirects', # Filter out redirects
    )

  def get_all_files(self):
    return self.get_with_continue('query', 'pages',
      generator='allimages',
      gailimit='500',
      prop='duplicatefiles', # Include info about duplicates
    )

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

import requests

class Wiki:
  def __init__(self, api_url):
    self.api_url = api_url
    self.lgtoken = None

    # As of MediaWiki 1.27, logging in and remaining logged in requires correct HTTP cookie handling by your client on all requests.
    self.session = requests.Session()

  def get(self, action, **kwargs):
    kwargs.update({
      'action': action,
      'format': 'json',
    })
    r = self.session.get(self.api_url, params=kwargs)
    if r.status_code >= 400 and r.status_code <= 499:
      print(kwargs)
      raise ValueError(f'Request to "{r.url}" failed with code {r.status_code}:\n{r.text}')
    return r.json()

  def get_with_continue(self, action, entry_key, **kwargs):
    while 1:
      data = self.get(action, **kwargs)
      try:
        entries = data[action][entry_key]
      except KeyError:
        print(f'Entry key "{entry_key}" was not found in data. Did you mean one of these keys: {data.keys()}')
        break

      for entry in entries:
        yield entry

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

  def get_csrf_token(self):
    # On any login request, maybe?
    return self.get('query', meta=tokens)['query']['tokens']['csrftoken']

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

  def get_all_pages(self):
    return self.get_with_continue('query', 'allpages',
      list='allpages',
      aplimit='500',
      apfilterredir='nonredirects', # Filter out redirects
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
      try:
        print(data['login']['result'])
      except KeyError:
        print(data['error']['code'])
        print(data['error']['info'])
      return False

    print(f'Successfully logged in as {username}')
    return True

import requests

class Wiki:
  def __init__(self, api_url):
    self.api_url = api_url

  def get(self, action, **kwargs):
    kwargs.update({
      'action': action,
      'format': 'json',
    })
    r = requests.get(self.api_url, kwargs)
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

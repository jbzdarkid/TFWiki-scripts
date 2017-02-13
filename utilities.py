from Queue import Queue
from threading import Thread, Event

wiki_api = r'https://wiki.teamfortress.com/w/api.php?action=query&format=json'
LANGS = ['ar', 'cs', 'da', 'de', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

# Asynchronous method to generate a list of pages. Queries the API for a list of pages, and signals via event when done.
def get_list(type):
  pages = Queue()
  done = Event()
  Thread(target=_get_list, args=(type, english, page_q, done)).start()
  return pages, done

def _get_list(type, page_q, done):
  if type == 'users':
    url = wiki_api + '&list=allusers&aulimit=500'
    query_key = 'allusers'
    continue_key = 'aufrom'
  elif type == 'pages':
    url = wiki_api + '&list=allpages&aplimit=500&apfilterredir=nonredirects'
    query_key = 'allpages'
    continue_key = 'apcontinue'
  elif type == 'english':
    url = wiki_api + '&list=allpages&aplimit=500&apfilterredir=nonredirects'
    query_key = 'allpages'
    continue_key = 'apcontinue'
    english = True
  elif type == 'templates':
    url = wiki_api + '&list=allpages&aplimit=500&apfilterredir=nonredirects&apnamespace=10'
    query_key = 'allpages'
    continue_key = 'apcontinue'

  while True:
		result = loads(urlopen(url.encode('utf-8')).read())
    for page in result['query'][query_key]:
      if type == 'english' and page['title'].rpartition('/')[2] in langs:
        continue
      if type == 'templates':
        if '/' in page['title']: # FIXME: Necessary?
          continue # Don't include subpages
        elif page['title'].partition('/')[0] == 'Template:Dictionary':
          continue # Don't include dictionary subpages
        elif page['title'].partition('/')[0] == 'Template:PatchDiff':
          continue # Don't include patch diffs.
        elif page['title'][:13] == 'Template:User':
          continue # Don't include userboxes.
      page_q.add(page['title'])
		if 'continue' in result:
      url = '%s&%s=%s' % (wiki_address, continue_key, result['continue'][continue_key])
		else:
      done.set()
      return

# Returns the number of embed calls for a template.
def whatlinkshere(page):
  link_count = 0
	url = wiki_api + r'&list=embeddedin&eifilterredir=nonredirects&eilimit=500&eititle=' + quote(page.encode('utf-8'))
  while True:
		result = loads(urlopen(url.encode('utf-8')).read())
		if 'continue' in result:
      link_count += len(result['query']['embeddedin'])
      url = '%s&%s=%s' % (wiki_address, continue_key, result['continue']['eicontinue'])
		else:
      return link_count

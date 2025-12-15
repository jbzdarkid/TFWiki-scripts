# A very light smattering of tests
import inspect
import sys
from datetime import datetime, UTC
from pathlib import Path

from wikitools.wiki import Wiki
from wikitools.page import Page
from wikitools.file_dict import FileDict
from reports.untranslated_templates import parse_lang_templates

class MockWiki(Wiki):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self.mock_wikitext = {}
    self.mock_recentchanges = {}

    for file in Path('cache/mock/').glob('**/*.txt'):
      file.unlink() # Clean up any cached state
    self.page_text_cache = FileDict('cache/mock/text')
    self.page_html_cache = FileDict('cache/mock/html')

  def get_namespaces(self):
    # This would usually incur a network call, so we mock it here.
    return {
      '*': '*',
    }

  def get(self, action, **params):
    if action == 'parse' and params['prop'] == 'wikitext':
      text = self.mock_wikitext[params['page']]
      return {'parse': {'wikitext': {'*': text} } }
    elif action == 'query' and params['list'] == 'recentchanges':
      pages = [{'title': title, 'timestamp': timestamp} for title, timestamp in self.mock_recentchanges.items()]
      return {'query': {'recentchanges': pages} }

    raise ValueError(f'action={action}: {params}')


class Tests:
  # Class setup
  wiki = MockWiki('https://wiki.example.com/w/api.php')
  wiki.MAX_RETRIES = 0

  #############
  #!# Tests #!#
  #############

  def test_lang_parser(self):
    p = Page(self.wiki, 'TestPage')
    self.wiki.mock_wikitext['TestPage'] = """{{lang
      | en = English
      | ru = Russian
    }}{{lang incomplete|en=[[Hi]] there|de=[[Hello/de|{{common string|hello}}]]}}
    {{some template|{{{lang|}}}
    """
    expected = [{
      'template': 'lang',
      'location': "''Line 1'': <nowiki>English</nowiki>",
      'args': [('en', 'English'), ('ru', 'Russian')],
    }, {
      'template': 'lang incomplete',
      'location': "''Line 4'': <nowiki>there</nowiki>",
      'args': [('en', 'there'), ('de', '')],
    }]

    actual = parse_lang_templates(p)
    assert expected[0] == actual[0], actual[0]
    assert expected[1] == actual[1], actual[1]

  def test_cache_invalidation(self):
    p = Page(self.wiki, 'Template:Foo')
    self.wiki.mock_wikitext['Template:Foo'] = 'a'
    print('Fetching from network...')
    assert p.get_wiki_text() == 'a'
    self.wiki.mock_wikitext.pop('Template:Foo')
    print('Fetching from cache...')
    assert p.get_wiki_text() == 'a'

    timestamp = datetime.now(UTC).isoformat()
    self.wiki.mock_recentchanges = {'Template:Foo': timestamp}
    self.wiki.update_caches_from_recent_changes()

    self.wiki.mock_wikitext['Template:Foo'] = 'b'
    print('Cache invalidated, freshly fetching from network...')
    assert p.get_wiki_text() == 'b'
    self.wiki.mock_wikitext.pop('Template:Foo')
    print('Fetching from cache again...')
    assert p.get_wiki_text() == 'b'


if __name__ == '__main__':
  tests = Tests()

  def is_test(method):
    return inspect.ismethod(method) and method.__name__.startswith('test')
  tests = list(inspect.getmembers(tests, is_test))
  tests.sort(key=lambda func: func[1].__code__.co_firstlineno)

  for test in tests:
    if len(sys.argv) > 1: # Requested specific test(s)
      if test[0] not in sys.argv[1:]:
        continue

    # Test setup (nothing yet)

    # Run test
    print('---', test[0], 'started')
    try:
      test[1]()
    except:
      print('!!!', test[0], 'failed:')
      import traceback
      traceback.print_exc()
      sys.exit(-1)

    print('===', test[0], 'passed')
  print('\nAll tests passed')

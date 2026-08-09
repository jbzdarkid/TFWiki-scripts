# A very light smattering of tests
import inspect
import sys
from pathlib import Path

from wikitools.wiki import Wiki
from wikitools.page import Page
from wikitools.file_dict import FileDict
from reports.untranslated_templates import parse_lang_templates
from reports.utils import utcnow

class MockWiki(Wiki):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self.mock_wikitext = {}
    self.mock_touched = {}
    self.mock_links = {}

    for file in Path('cache/mock/').glob('**/*.txt'):
      file.unlink() # Clean up any cached state
    self.page_text_cache = FileDict('cache/mock/text')
    self.page_html_cache = FileDict('cache/mock/html')
    self.page_link_cache = FileDict('cache/mock/link')

  def get_namespaces(self):
    # This would usually incur a network call, so we mock it here.=
    self.content_namespaces = ['Main']
    class IdentityDict:
      def __getitem__(self, key):
        return key
    return IdentityDict()

  def get(self, action, **params):
    if action == 'parse' and params['prop'] == 'wikitext':
      text = self.mock_wikitext[params['page']]
      return {'parse': {'wikitext': {'*': text} } }
    elif action == 'query' and params['generator'] == 'allpages':
      pages = [{'title': title, 'touched': touched} for title, touched in self.mock_touched.items()]
      return {'query': {'pages': pages} }
    elif action == 'query' and params['generator'] == 'links':
      links = self.mock_links.get(params['titles'], [])
      return {'query': {'pages': [{'title': title} for title in links]} }

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
    print('Fetching from network...')
    self.wiki.mock_wikitext['Template:Foo'] = 'a'
    assert p.get_wiki_text() == 'a'

    print('Fetching from cache...')
    self.wiki.mock_wikitext.pop('Template:Foo')
    assert p.get_wiki_text() == 'a'

    timestamp = utcnow().replace(tzinfo=None).isoformat()
    self.wiki.mock_touched = {'Template:Foo': timestamp}
    self.wiki.populate_touched_cache()

    print('Cache invalidated, freshly fetching from network...')
    self.wiki.mock_wikitext['Template:Foo'] = 'b'
    assert p.get_wiki_text() == 'b'

    print('Fetching from cache again...')
    self.wiki.mock_wikitext.pop('Template:Foo')
    assert p.get_wiki_text() == 'b'

  def test_cache_subkeys(self):
    p = Page(self.wiki, 'Template:Foo')
    def assert_links(namespace, expected):
      actual = list(p.get_links(namespaces=[namespace]))
      expected = [Page(self.wiki, expected)]
      assert expected == actual, actual

    print('Fetching from network...')
    self.wiki.mock_links['Template:Foo'] = ['a']
    assert_links('1', 'a')
    self.wiki.mock_links['Template:Foo'] = ['b']
    assert_links('2', 'b')

    print('Fetching from cache...')
    self.wiki.mock_links.pop('Template:Foo')
    assert_links('1', 'a')
    assert_links('2', 'b')

    timestamp = utcnow().replace(tzinfo=None).isoformat()
    self.wiki.mock_touched = {'Template:Foo': timestamp}
    self.wiki.populate_touched_cache()

    print('Cache invalidated, freshly fetching from network...')
    self.wiki.mock_links['Template:Foo'] = ['c']
    assert_links('1', 'c')
    self.wiki.mock_links['Template:Foo'] = ['d']
    assert_links('2', 'd')

    print('Fetching from cache again...')
    self.wiki.mock_links.pop('Template:Foo')
    assert_links('1', 'c')
    assert_links('2', 'd')

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

# A very light smattering of tests
import inspect
import sys
from wikitools.wiki import Wiki
from wikitools.page import Page
from reports.untranslated_templates import parse_lang_templates

class MockWiki(Wiki):
  def get_namespaces(self):
    return {} # This would usually incur a network call, so we mock it here.


class Tests:
  # Class setup
  wiki = MockWiki('https://wiki.example.com/w/api.php')

  #############
  #!# Tests #!#
  #############

  def test_lang_parser(self):
    p = Page(self.wiki, 'TestPage')
    self.wiki.page_text_cache[p.title] = """{{lang
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

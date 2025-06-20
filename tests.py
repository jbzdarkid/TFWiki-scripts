# A very light smattering of tests
import inspect
import sys
from wikitools.wiki import Wiki
from wikitools.page import Page
from reports.untranslated_templates import parse_lang_templates, parse_lang_templates2

class MockWiki(Wiki):
  def get_namespaces(self):
    return {}


raw_text = """{{lang incomplete
| en = (
| ja = （
| zh-hans = （
| zh-hant = （
}}{{{1}}}{{lang incomplete
| en = )
| ja = ）
| zh-hans = ）
| zh-hant = ）
}}<noinclude>

{{Doc begin}}
== Usage ==
:<code><nowiki>{{Parenthesis|1}}</nowiki></code>
Replace "1" with the message you need in parenthesis. Localised for Japanese and Traditional/Simplified Chinese. Otherwise uses standard English parentheses.

== Example ==
{{tlx|Parenthesis|Hello Wiki!}} produces {{Parenthesis|Hello Wiki!}}

[[Category:Formatting templates|Parenthesis]]
</noinclude>"""

class Tests:
  # Class setup

  #############
  #!# Tests #!#
  #############

  def test_lang_parser(self):
    w = MockWiki('https://wiki.teamfortress.com/w/api.php')
    p = Page(w, 'Template:Parenthesis')
    for text in [raw_text]:
      w.page_text_cache[p.title] = text
      l1 = parse_lang_templates(p)
      l2 = parse_lang_templates2(p)
      assert len(l1) == len(l2), f'{len(l1)} != {len(l2)}\n{l1}\n{l2}'
      for i in range(len(l1)):
        assert l1[i]['template'] == l2[i]['template'], f'{l1[i]["template"]} != {l2[i]["template"]}'
        assert l1[i]['location'] == l2[i]['location'], f'{l1[i]["location"]}\n!=\n{l2[i]["location"]}'
        assert l1[i]['args'] == l2[i]['args']


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
    except Exception:
      print('!!!', test[0], 'failed:')
      import traceback
      traceback.print_exc()
      sys.exit(-1)

    print('===', test[0], 'passed')
  print('\nAll tests passed')

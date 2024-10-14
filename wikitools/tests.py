# A very light smattering of tests
import inspect
import sys

from page import Page

class MockWiki:
  def __init__(self):
    pass
  
class Tests:
  # Class setup
  wiki = MockWiki()

  # Utilities
  def sort_titles(self, titles):
    pages = [Page(self.wiki, title) for title in titles]
    pages.sort()
    return [page.title for page in pages]

  #############
  #!# Tests #!#
  #############
  def test_sort_pages(self):
    actual =  self.sort_titles(['Scout/zh-hans', 'Scout/ru', 'Scout/pt-br', 'Scout/es', 'Scout', 'Scout/fr', 'Scout/it'])
    expected = ['Scout', 'Scout/es', 'Scout/fr', 'Scout/it', 'Scout/pt-br', 'Scout/ru', 'Scout/zh-hans']
    assert expected == actual, f'{expected}\n{actual}'
    actual = self.sort_titles(['Scout', 'Solider', 'Pyro', 'Demoman', 'Heavy', 'Engineer', 'Medic', 'Sniper', 'Spy'])
    expected = ['Demoman', 'Engineer', 'Heavy', 'Medic', 'Pyro', 'Scout', 'Sniper', 'Solider', 'Spy']
    assert expected == actual, f'{expected}\n{actual}'
    actual = self.sort_titles(['Scout/ko', 'Solider/ja', 'Pyro/it', 'Demoman/hu', 'Heavy/fr', 'Engineer/de', 'Medic/cs', 'Sniper/ar', 'Spy'])
    expected = ['Spy', 'Sniper/ar', 'Medic/cs', 'Engineer/de', 'Heavy/fr', 'Demoman/hu', 'Pyro/it', 'Solider/ja', 'Scout/ko']
    assert expected == actual, f'{expected}\n{actual}'

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

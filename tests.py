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

  # TODO: Define tests here (which start with the word test)

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

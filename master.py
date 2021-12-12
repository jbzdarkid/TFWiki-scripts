from datetime import datetime
import importlib
from os import environ
from sys import argv, stdout
from traceback import print_exc
from wikitools import wiki
from wikitools.page import Page

# I need to extend the translation list to include categories (and the missing list)
#   Add this as a separate report, then link between them
# A report for 'missing navbox usage', i.e. navboxes which link to pages which don't include said navboxes.
#   Might need a list of navboxes, though.
# Write a replacement script for broken external links
#   forums.tfmaps.net?t=# -> tf2maps.net/threads/#
# Sort external links by domain (with sub-headers)
# External links is a mess. It needs a modern eye.
# update readme (again)

def publish_single_report(w, module, report_name):
  start = datetime.now()
  try:
    main = importlib.import_module(module).main
    print(Page(w, f'{root}/{report_name}').edit(main(w), bot=True, summary=summary))
    end = datetime.now()
    print(f'Report {report_name} took {end - start}')
    return 0
  except Exception:
    print(f'Failed to update {report_name}')
    print_exc(file=stdout)
    return 1

def publish_lang_report(w, module, report_name):
  start = datetime.now()
  try:
    main = importlib.import_module(module).main
    for lang, output in main(w):
      print(Page(w, f'{root}/{report_name}/{lang}').edit(output, bot=True, summary=summary))
    end = datetime.now()
    print(f'Report {report_name} took {end - start}')
    return 0
  except Exception:
    print(f'Failed to update {report_name}')
    print_exc(file=stdout)
    return 1

if __name__ == '__main__':
  if argv[1] == 'schedule':
    root = 'Team Fortress Wiki:Reports'
    is_daily = True
    is_weekly = datetime.now().weekday() == 0 # Monday
    is_monthly = datetime.now().day == 1 # 1st of every month
    summary = 'Automatic update via https://github.com/jbzdarkid/TFWiki-scripts'
  elif argv[1] == 'workflow_dispatch':
    root = 'User:Darkid/Reports'
    is_daily = True
    is_weekly = True
    is_monthly = True
    summary = 'Test update via https://github.com/jbzdarkid/TFWiki-scripts'
  elif argv[1] == 'pull_request':
    root = 'User:Darkid/Reports'
    is_daily = True
    is_weekly = True
    is_monthly = False
    summary = 'Test update via https://github.com/jbzdarkid/TFWiki-scripts'
  else:
    print(f'Not sure what to run in response to {argv[1]}')
    exit(1)

  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  if not w.login(environ['WIKI_USERNAME'], environ['WIKI_PASSWORD']):
    exit(1)
  print(datetime.now())
  failures = 0

  if is_daily:
    failures += publish_lang_report(w, 'untranslated_templates', 'Untranslated templates')
    failures += publish_lang_report(w, 'missing_translations', 'Missing translations')
    # failures += publish_lang_report(w, 'missing_categories', 'Untranslated categories')
    failures += publish_lang_report(w, 'all_articles', 'All articles')

  if is_weekly:
    failures += publish_single_report(w, 'wanted_templates', 'Wanted templates')
    failures += publish_single_report(w, 'navboxes', 'Pages which are missing navboxes')
    failures += publish_single_report(w, 'overtranslated', 'Pages with no english equivalent')
    failures += publish_single_report(w, 'incorrectly_categorized', 'Pages with incorrect categorization')

  if is_monthly:
    failures += publish_single_report(w, 'duplicate_files', 'Duplicate files')
    failures += publish_single_report(w, 'unused_files', 'Unused files')
    failures += publish_single_report(w, 'edit_stats', 'Users by edit count')
    failures += publish_single_report(w, 'undocumented_templates', 'Undocumented templates')
    failures += publish_single_report(w, 'external_links', 'External links')
    failures += publish_single_report(w, 'mismatched', 'Mismatched parenthesis') # This report is very slow, so it goes last.

  exit(failures)

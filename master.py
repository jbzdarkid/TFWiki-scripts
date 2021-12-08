from datetime import datetime
import importlib
from os import environ
from sys import argv
from wikitools import wiki
from wikitools.page import Page
from traceback import print_exc

# I would like to write a script which scrapes Special:WantedTemplates to check for Templates which are used in (Main).
# I would like to write a script which identifies miscategorized pages (lang pages in non-eng categories and vice-versa)

def publish_single_report(w, module, report_name):
  try:
    main = importlib.import_module(module).main
    print(Page(w, f'{root}/{report_name}').edit(main(), bot=True, summary=summary))
    print(datetime.now())
    return 0
  except Exception:
    print(f'Failed to update {report_name}')
    print_exc()
    return 1

def publish_lang_report(w, module, report_name):
  try:
    main = importlib.import_module(module).main
    for lang, output in main():
      print(Page(w, f'{root}/{report_name}/{lang}').edit(output, bot=True, summary=summary))
    print(datetime.now())
    return 0
  except Exception:
    print(f'Failed to update {report_name}')
    print_exc()
    return 1

if __name__ == '__main__':
  if argv[1] == 'workflow_dispatch':
    root = 'User:Darkid/Reports'
    is_daily = True
    is_weekly = True
    is_monthly = True
    summary = 'Test update via https://github.com/jbzdarkid/TFWiki-scripts'
  elif argv[1] == 'schedule':
    # root = 'Team Fortress Wiki:Reports'
    root = 'User:Darkid/Reports'
    is_daily = True
    is_weekly = datetime.now().weekday() == 0 # Monday
    is_monthly = datetime.now().day == 1 # 1st of every month
    summary = 'Automatic update via https://github.com/jbzdarkid/TFWiki-scripts'
  else:
    print(f'Not sure what to run in response to {argv[1]}')
    exit(1)

  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  if not w.login(environ['WIKI_USERNAME'], environ['WIKI_PASSWORD']):
    exit(1)
  print(datetime.now())
  failures = 0
  print(f'Daily: {is_daily} Weekly: {is_weekly} Monthly: {is_monthly}')

  if is_daily:
    failures += publish_lang_report(w, 'untranslated_templates', 'Untranslated templates')
    failures += publish_lang_report(w, 'missing_translations', 'Missing translations')
    failures += publish_lang_report(w, 'all_articles', 'All Articles')

  if is_daily or is_weekly:
    pass

  if is_daily or is_weekly or is_monthly:
    failures += publish_single_report(w, 'edit_stats', 'Users by edit count')
    failures += publish_single_report(w, 'undocumented_templates', 'Undocumented templates')
    failures += publish_single_report(w, 'unused_files', 'Unused files')
    failures += publish_single_report(w, 'duplicate_files', 'Duplicate files')
    failures += publish_single_report(w, 'external_links', 'External links')
    failures += publish_single_report(w, 'mismatched', 'Mismatched parenthesis')

  exit(failures)

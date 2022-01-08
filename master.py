from datetime import datetime, timedelta
import importlib
from os import environ
from sys import argv, stdout
from traceback import print_exc
from wikitools import wiki
from wikitools.page import Page

# Write a replacement script for broken external links -> WindBOT filter
#   forums.tfmaps.net?t=# -> tf2maps.net/threads/#
# Sort external links by domain (with sub-headers)
# External links is a mess. It needs a modern eye.
# update readme (again)
# Now that I have wikitext caching, many things are faster. Write a report for Redirects which link to non-existant subsections

diff_links = []

def publish_single_report(w, module, report_name):
  start = datetime.now()
  print(f'Started {report_name} at {start}')
  try:
    main = importlib.import_module(module).main
    diff_link = Page(w, f'{root}/{report_name}').edit(main(w), bot=True, summary=summary)
    diff_links.append((report_name, datetime.now() - start, {'en': diff_link}))
    return 0
  except Exception:
    print(f'Failed to update {report_name}')
    print_exc(file=stdout)
    return 1

def publish_lang_report(w, module, report_name):
  start = datetime.now()
  print(f'Started {report_name} at {start}')
  try:
    main = importlib.import_module(module).main
    diff_link_map = {}
    for lang, output in main(w):
      diff_link = Page(w, f'{root}/{report_name}/{lang}').edit(output, bot=True, summary=summary)
      diff_link_map[lang] = diff_link
    diff_links.append((report_name, datetime.now() - start, diff_link_map))
    return 0
  except Exception:
    print(f'Failed to update {report_name}')
    print_exc(file=stdout)
    return 1

if __name__ == '__main__':
  event = environ.get('GITHUB_EVENT_NAME', 'local_run')
  if event == 'schedule':
    root = 'Team Fortress Wiki:Reports'
    is_daily = True
    is_weekly = datetime.now().weekday() == 0 # Monday
    is_monthly = datetime.now().day == 1 # 1st of every month
    summary = 'Automatic update via https://github.com/jbzdarkid/TFWiki-scripts'
  elif event == 'workflow_dispatch':
    root = 'User:Darkid/Reports'
    is_daily = True
    is_weekly = True
    is_monthly = True
    summary = 'Test update via https://github.com/jbzdarkid/TFWiki-scripts'
  elif event == 'pull_request':
    root = 'User:Darkid/Reports'
    is_daily = True
    is_weekly = True
    is_monthly = False
    summary = 'Test update via https://github.com/jbzdarkid/TFWiki-scripts'
  elif event == 'local_run':
    root = 'Team Fortress Wiki:Reports'
    summary = 'Test update via https://github.com/jbzdarkid/TFWiki-scripts'
    w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
    failures = 0
    failures += publish_lang_report(w, 'untranslated_templates', 'Untranslated templates')
    failures += publish_lang_report(w, 'missing_translations', 'Missing translations')
    failures += publish_lang_report(w, 'missing_categories', 'Untranslated categories')
    failures += publish_lang_report(w, 'all_articles', 'All articles')
    failures += publish_single_report(w, 'wanted_templates', 'Wanted templates')
    failures += publish_single_report(w, 'navboxes', 'Pages which are missing navboxes')
    failures += publish_single_report(w, 'overtranslated', 'Pages with no english equivalent')
    print(f'{failures} failed')
    exit(failures)

  else:
    print(f'Not sure what to run in response to {event}')
    exit(1)

  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  if not w.login(environ['WIKI_USERNAME'], environ['WIKI_PASSWORD']):
    exit(1)
  failures = 0

  if is_daily: # Multi-language reports need frequent updates since we have many translators
    failures += publish_lang_report(w, 'untranslated_templates', 'Untranslated templates')
    failures += publish_lang_report(w, 'missing_translations', 'Missing translations')
    failures += publish_lang_report(w, 'missing_categories', 'Untranslated categories')
    failures += publish_lang_report(w, 'all_articles', 'All articles')

  if is_weekly: # English (or cross-language) reports which are not too costly to run
    failures += publish_single_report(w, 'wanted_templates', 'Wanted templates')
    failures += publish_single_report(w, 'navboxes', 'Pages which are missing navboxes')
    failures += publish_single_report(w, 'overtranslated', 'Pages with no english equivalent')

  if is_monthly: # Expensive or otherwise infrequently-changing reports
    failures += publish_single_report(w, 'incorrectly_categorized', 'Pages with incorrect categorization')
    failures += publish_single_report(w, 'duplicate_files', 'Duplicate files')
    failures += publish_single_report(w, 'unused_files', 'Unused files')
    failures += publish_single_report(w, 'undocumented_templates', 'Undocumented templates')
    failures += publish_single_report(w, 'edit_stats', 'Users by edit count')
    failures += publish_single_report(w, 'external_links', 'External links')
    failures += publish_single_report(w, 'mismatched', 'Mismatched parenthesis')
    failures += publish_single_report(w, 'displaytitles', 'Duplicate displaytitles')

  comment = 'Please verify the following diffs:\n'
  for report_name, duration, link_map in diff_links:
    duration -= timedelta(microseconds=duration.microseconds) # Strip microseconds
    comment += f'- [ ] {report_name} ran in {duration}:'
    languages = sorted(link_map.keys(), key=lambda lang: (lang != 'en', lang)) # Sort languages, keeping english first
    for language in languages:
      comment += f' [{language}]({link_map[language]})'
    comment += '\n'

  # Pass this as output to github-actions, so it can be used in later steps
  with open(environ['GITHUB_ENV'], 'a') as f:
    f.write(f'GITHUB_COMMENT<<EOF\n{comment}\nEOF\n')

  exit(failures)

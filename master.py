from datetime import datetime, timedelta
import importlib
from os import environ
from subprocess import run, PIPE
from sys import argv, stdout
from traceback import print_exc
from wikitools import wiki
from wikitools.page import Page

# Write a replacement script for broken external links -> WindBOT filter
#   forums.tfmaps.net?t=# -> tf2maps.net/threads/#
# Sort external links by domain (with sub-headers)
# External links is a mess. It needs a modern eye.
# update readme (again)
# Improve the wikitools/wiki get_with_continue to actually yield the pagenames, not just the json objects.

diff_links = []

def publish_report(w, module, report_name):
  start = datetime.now()
  try:
    report_output = importlib.import_module(module).main(w)
    diff_link_map = {}

    if isinstance(report_output, list):
      for lang, output in report_output:
        diff_link_map[lang] = Page(w, f'{root}/{report_name}/{lang}').edit(output, bot=True, summary=summary)
    else:
      diff_link_map['en'] = Page(w, f'{root}/{report_name}').edit(output, bot=True, summary=summary)

    diff_links.append((report_name, datetime.now() - start, diff_link_map))
    return 0
  except Exception:
    print(f'Failed to update {report_name}')
    print_exc(file=stdout)
    return 1

all_reports = {
  'untranslated_templates': 'Untranslated templates',
  'missing_translations': 'Missing translations',
  'missing_categories': 'Untranslated categories',
  'all_articles': 'All articles',
  'wanted_templates': 'Wanted templates',
}

if __name__ == '__main__':
  event = environ['GITHUB_EVENT_NAME']
  if event == 'schedule':
    root = 'Team Fortress Wiki:Reports'
    summary = 'Automatic update via https://github.com/jbzdarkid/TFWiki-scripts'

    # Multi-language reports need frequent updates since we have many translators
    reports_to_run = ['untranslated_templates', 'missing_transations', 'missing_categories', 'all_articles']
    if datetime.now().weekday() == 0: # Every Monday, run english-only (or otherwise less frequently needed) reports
      reports_to_run += ['wanted_templates', 'navboxes', 'overtranslated']
    if datetime.now().day == 1 # On the 1st of every month, run everything
      reports_to_run = all_reports.keys()

  elif event == 'pull_request':
    root = 'User:Darkid/Reports'
    summary = 'Test update via https://github.com/jbzdarkid/TFWiki-scripts'

    merge_base = run(['git', 'merge-base', 'HEAD', environ['GITHUB_BASE_REF'], text=True, stdout=PIPE).stdout.strip()
    diff = run(['git', 'diff-index', 'HEAD', merge_base], text=True, stdout=PIPE).stdout.strip()

    # somehow turn that output into a bunch of files, idk man


  elif event == 'workflow_dispatch':
    root = 'User:Darkid/Reports'
    summary = 'Test update via https://github.com/jbzdarkid/TFWiki-scripts'
    reports_to_run = all_reports.keys() # On manual triggers, run everything

  else:
    print(f'Not sure what to run in response to {event}')
    exit(1)

  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  if not w.login(environ['WIKI_USERNAME'], environ['WIKI_PASSWORD']):
    exit(1)
  failures = 0

  for report in lang_reports:
    failures += publish_lang_report(w, report['file'], report['title'])
  for report in single_reports:
    failures += publish_single_report(w, report['file'], report['title'])

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

from datetime import datetime, timedelta
import importlib
from os import environ
from subprocess import check_output
from sys import stdout
from traceback import print_exc
from wikitools import wiki
from wikitools.page import Page

import open_pr_comment

# Reports I want:
# Now that I have wikitext caching, many things are faster. Write a report for Redirects which link to non-existant subsections
# images without licensing?
# Quotations which use quote characters
# external links is basically a whole new report FWIW
# Using {{lang}} and {{if lang}} on non-template pages
# Direct links to disambig pages

# Reports I want to improve:
# update readme (again)
# Consider running some scripts against the Help: namespace, too
# (like what? miscategorized, mismatched, uhhh)
# Sort missing categories by # pages
# Sort the output from mismatched
# Sort the output from displaytitles
# Threading for navboxes.py?
# Ensure that PRs which add files also touch readme.md

def handle_failed_edits(link_map, report_output, report_name):
  report_name = report_name.lower().replace(' ', '_')
  if isinstance(report_output, str) and link_map['en'] is None:
    with open(f'wiki_{report_name}.txt', 'w', encoding='utf-8') as f:
      f.write(report_output)
  else:
    for lang, output in report_output:
      if link_map[lang] is None:
        with open(f'wiki_{report_name}_{lang}.txt', 'w', encoding='utf-8') as f:
          f.write(output)

def publish_report(w, module, report_name, root, summary):
  link_map = {}
  try:
    report_output = importlib.import_module(module).main(w)

    if isinstance(report_output, list):
      for lang, output in report_output:
        link_map[lang] = Page(w, f'{root}/{report_name}/{lang}').edit(output, bot=True, summary=summary)
    else:
      link_map['en'] = Page(w, f'{root}/{report_name}').edit(report_output, bot=True, summary=summary)

    handle_failed_edits(link_map, report_output, report_name)

  except Exception:
    print(f'Failed to update {report_name}')
    print_exc(file=stdout)

  return link_map

all_reports = {
  'untranslated_templates': 'Untranslated templates',
  'missing_translations': 'Missing translations',
  'missing_categories': 'Untranslated categories',
  'all_articles': 'All articles',
  'wanted_templates': 'Wanted templates',
  'navboxes': 'Pages which are missing navboxes',
  'overtranslated': 'Pages with no english equivalent',
  'incorrectly_categorized': 'Pages with incorrect categorization',
  'incorrectly_linked': 'Pages with incorrect links',
  'duplicate_files': 'Duplicate files',
  'unused_files': 'Unused files',
  'undocumented_templates': 'Undocumented templates',
  'edit_stats': 'Users by edit count',
  'external_links2': 'External links',
  'mismatched': 'Mismatched parenthesis',
  'displaytitles': 'Duplicate displaytitles',
}

if __name__ == '__main__':
  event = environ.get('GITHUB_EVENT_NAME', 'local_run')
  modules_to_run = []

  if event == 'schedule':
    root = 'Team Fortress Wiki:Reports'
    summary = 'Automatic update via https://github.com/jbzdarkid/TFWiki-scripts'

    # Multi-language reports need frequent updates since we have many translators
    modules_to_run += ['untranslated_templates', 'missing_translations', 'all_articles']
    if datetime.now().weekday() == 0: # Every Monday, run english-only (or otherwise less frequently needed) reports
      modules_to_run += ['wanted_templates', 'navboxes', 'overtranslated', 'missing_categories', 'incorrectly_categorized']
    if datetime.now().day == 1: # On the 1st of every month, run everything
      modules_to_run = all_reports.keys()

  elif event == 'pull_request':
    root = 'User:Darkid/Reports'
    summary = 'Test update via https://github.com/jbzdarkid/TFWiki-scripts'

    merge_base = check_output(['git', 'merge-base', 'HEAD', 'origin/' + environ['GITHUB_BASE_REF']], text=True).strip()
    diff = check_output(['git', 'diff', '--name-only', merge_base], text=True).strip()
    for row in diff.split('\n'):
      file = row.replace('.py', '').strip()
      if file in all_reports:
        modules_to_run.append(file)

  elif event == 'workflow_dispatch':
    root = 'User:Darkid/Reports'
    summary = 'Test update via https://github.com/jbzdarkid/TFWiki-scripts'
    modules_to_run = all_reports.keys() # On manual triggers, run everything

  elif event == 'local_run':
    w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
    for report in all_reports:
      # Root and summary don't matter because we can't publish anyways.
      publish_report(w, report, all_reports[report], '', '')
    exit(0)

  else:
    print(f'Not sure what to run in response to {event}')
    exit(1)

  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  if not w.login(environ['WIKI_USERNAME'], environ['WIKI_PASSWORD']):
    exit(1)

  comment = 'Please verify the following diffs:\n'
  succeeded = True

  for module in modules_to_run:
    report_name = all_reports[module]
    start = datetime.now()
    link_map = publish_report(w, module, report_name, root, summary)
    duration = datetime.now() - start
    duration -= timedelta(microseconds=duration.microseconds) # Strip microseconds
    if not link_map:
      action_url = 'https://github.com/' + environ['GITHUB_REPOSITORY'] + '/actions/runs/' + environ['GITHUB_RUN_ID']
      comment += f'- [ ] {report_name} failed after {duration}: {action_url}\n'
      succeeded = False
    else:
      comment += f'- [ ] {report_name} succeeded in {duration}:'
      languages = sorted(link_map.keys(), key=lambda lang: (lang != 'en', lang)) # Sort languages, keeping english first
      for language in languages:
        link = link_map.get(language, None)
        if link:
          comment += f' [{language}]({link_map[language]})'
        else:
          comment += f' ~~[{language}](## "Upload failed")~~'
      comment += '\n'

  if event == 'pull_request':
    open_pr_comment.create_pr_comment(comment)
  elif event == 'workflow_dispatch':
    open_pr_comment.create_issue('Workflow dispatch finished', comment)
  elif environ['GITHUB_EVENT_NAME'] == 'schedule':
    print(comment)

  exit(0 if succeeded else 1)

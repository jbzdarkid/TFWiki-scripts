import importlib
from datetime import datetime, timedelta, timezone
from os import environ
from random import shuffle
from subprocess import check_output
from sys import argv, stdout
from time import sleep
from traceback import print_exc
from wikitools import wiki
from wikitools.page import Page

import open_pr_comment

# Reports I want:
# Now that I have wikitext caching, many things are faster. Write a report for Redirects which link to non-existant subsections
# Quotations which use quote characters
# Using {{lang}} and {{if lang}} on non-template pages -> this is apparently somewhat common now to make copy/paste editing easier
# Pages which link to disambig pages not in hatnote/see also
# Just... a summary of every single external link. Maybe just 'count per domain' and then list the top 10 pages? I'm finding a LOT of sus links, and it's only the ones that are *broken*.
# Templates sorted by usage and protect status
# A 'missing translations' report but for dictionary entries (maybe sorted by usage, too?)
# Templates which have redirects in them
# Main (or just non-Template) pages which use <includeonly> <onlyinclude> etc.

# Reports I want to improve:
# Sort missing categories by # pages
# Threading for navboxes.py?
# Might be more smarts to do in lang_quality.py, e.g. non-ascii characters in 'en', or check for only quote characters (or other lang incomplete hints)

def edit_or_save(page_name, file_name, lang, contents, summary):
  wiki_diff_url = Page(w, page_name).edit(contents, bot=True, summary=summary)
  if wiki_diff_url:
    return f' [{lang}]({wiki_diff_url})'

  # Edit failed, fall back to saving to file (will be attached as a build artifact)
  with open(f'reports/{file_name}', 'w', encoding='utf-8') as f:
    f.write(contents)

  action_url = 'https://github.com/' + environ['GITHUB_REPOSITORY'] + '/actions/runs/' + environ['GITHUB_RUN_ID']
  return f' ~~[{lang}]({action_url})~~'

  return None

def run_report(w, module, name):
  start = datetime.now(timezone.utc)
  print(f'Starting {name} at {start}')
  try:
    return importlib.import_module('reports.' + module).main(w)
  except Exception:
    print_exc(file=stdout)
    return None
  finally:
    duration = datetime.now(timezone.utc) - start
    duration -= timedelta(microseconds=duration.microseconds) # Strip microseconds
    print(f'Report {name} completed after {duration}')

# Multi-language reports need frequent updates since we have many translators
daily_reports = {
  'active_discussions': 'Active discussions',
  'all_articles': 'All articles',
  'missing_translations': 'Missing translations',
  'untranslated_templates': 'Untranslated templates',
}

# English-only but otherwise frequently changing reports
weekly_reports = {
  'displaytitles_weekly': 'Duplicate displaytitles',
  'incorrect_redirects': 'Mistranslated redirects',
  'incorrectly_categorized': 'Pages with incorrect categorization',
  'incorrectly_linked': 'Pages with incorrect links',
  'lang_duplicates': 'Lang duplicates',
  # 'lang_quality': 'Lang errors', # Disabled 2026-03-18 due to timeouts
  'mismatched_weekly': 'Mismatched parenthesis',
  'missing_categories': 'Untranslated categories',
  'missing_translations_weekly': 'Missing translations/sorted',
  'navboxes': 'Pages which are missing navboxes',
  'overtranslated': 'Pages with no english equivalent',
  'wanted_templates': 'Wanted templates',
}

# Everything else (especially reports which require all HTML contents)
monthly_reports = {
  'displaytitles': 'Duplicate displaytitles',
  'duplicate_files': 'Duplicate files',
  'edit_stats': 'Users by edit count',
  'external_links2': 'External links',
  'mismatched': 'Mismatched parenthesis',
  'undocumented_templates': 'Undocumented templates',
  'unlicensed_images': 'Unlicensed images',
  'unused_files': 'Unused files',
}

all_reports = daily_reports | weekly_reports | monthly_reports

if __name__ == '__main__':
  event = environ.get('GITHUB_EVENT_NAME', 'local_run')
  modules_to_run = []

  if event == 'schedule':
    root = 'Team Fortress Wiki:Reports'
    summary = 'Automatic update via https://github.com/jbzdarkid/TFWiki-scripts'

    # Determine which reports to run -- note that the weekly and monthly cadences don't necessarily line up.
    modules_to_run += daily_reports.keys()
    if datetime.now(timezone.utc).weekday() == 0:
      modules_to_run += weekly_reports.keys()
    if datetime.now(timezone.utc).day == 1:
      modules_to_run += monthly_reports.keys()

  elif event == 'pull_request':
    root = 'User:Darkid/Reports'
    summary = 'Test update via https://github.com/jbzdarkid/TFWiki-scripts'

    touched_readme = False
    touched_master = False
    created_report = False
    touched_reports = set()

    merge_base = check_output(['git', 'merge-base', 'HEAD', 'origin/' + environ['GITHUB_BASE_REF']], text=True).strip()
    output = check_output(['git', 'diff', '--name-status', '--no-renames', merge_base], text=True).strip()
    for line in output.split('\n'):
      status, file = line.split('\t')[:2]
      if file == 'README.md':
        touched_readme = True
      elif file == 'master.py':
        touched_master = True

      elif file.startswith('reports/'):
        if status == 'A':
          created_report = True
        if status in 'AMC': # Run all reports which were added, modified, or copied
          report_name = file[8:-3]
          touched_reports.add(report_name)

    print('Touched reports:', touched_reports)

    if created_report and not (touched_readme and touched_master):
      raise ValueError('When adding a new report, you must update the readme and master.py')

    for report in touched_reports:
      weekly_report = report + '_weekly'
      if weekly_report in all_reports:
        modules_to_run.append(weekly_report)
      elif report in all_reports:
        modules_to_run.append(report)

  elif event == 'workflow_dispatch':
    root = 'Team Fortress Wiki:Reports'
    summary = 'Manually triggered update from https://github.com/jbzdarkid/TFWiki-scripts'

    # On manual triggers, run everything, unless a specific report was specified.
    modules_to_run = argv[1].split(' ') if len(argv) > 1 else all_reports.keys()

  elif event == 'local_run':
    print('Local run; executing all reports')
    w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
    for report in all_reports:
      # Run the report but don't try to upload it, since we're not logged in.
      run_report(w, report, all_reports[report])
    exit(0)

  else:
    print(f'Not sure what to run in response to {event}')
    exit(1)

  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php', environ['USER_AGENT'])
  if not w.login(environ['WIKI_USERNAME'], environ['WIKI_PASSWORD']):
    exit(1)

  print('Successfully logged in, fetching RC log to invalidate the cache')
  w.update_caches_from_recent_changes()

  # I am working on a caching story, but it's not 100% ready yet.
  # Until then, shuffle the order of reports to guarantee a more even coverage,
  # when reports time out.
  modules_to_run = list(modules_to_run)
  shuffle(modules_to_run)
  print(f'Running reports: {modules_to_run}')

  # All scripts must finish with enough time to sleep and *then* upload the report files.
  # This value (on the global wiki class) acts as a soft stop for our reports,
  # so they are unable to make network requests after this time.
  # I'm just using a flat 30 minutes here, while accounting for 10 minutes before the actual github timelimit.
  sleep_before_upload = timedelta(minutes=30)
  w.last_network_request_time = datetime.now(timezone.utc) + timedelta(hours=5, minutes=40) - sleep_before_upload

  report_outputs = {}
  for module in modules_to_run:
    report_name = all_reports[module]
    report_outputs[report_name] = run_report(w, module, report_name)

  print('All reports completed, sleeping then uploading outputs')
  sleep(sleep_before_upload.total_seconds())

  w.last_network_request_time = None # Unblock network requests so we can POST again.
  w.MAX_RETRIES = 2 # Only 2 attempts at POST-ing. I think it's just working and returning 502, not actually faililng.

  comment = 'Please verify the following diffs:\n'
  for report_name, output in report_outputs.items():
    if not output:
      comment += f'- [ ] Report {report_name} threw an exception. Please check the action logs.\n'
      continue
    comment += f'- [ ] Report {report_name} succeeded, diffs:'
    file_name = 'wiki_' + report_name.lower().replace(' ', '_')
    if isinstance(output, list):
      for lang, contents in output:
        comment += edit_or_save(f'{root}/{report_name}/{lang}', f'{file_name}_{lang}.txt', lang, contents, summary)
    else:
      comment += edit_or_save(f'{root}/{report_name}', f'{file_name}.txt', 'en', output, summary)
    comment += '\n'

  if event == 'pull_request':
    open_pr_comment.create_pr_comment(comment)
  elif event == 'workflow_dispatch':
    open_pr_comment.create_issue('Workflow dispatch finished', comment)
  elif environ['GITHUB_EVENT_NAME'] == 'schedule':
    print(comment)

  num_failures = list(report_outputs.values()).count(None)
  exit(num_failures)

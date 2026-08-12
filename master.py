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

def run_report(w, module, name):
  start = datetime.now(timezone.utc)
  print(f'Starting {name} at {start}')
  try:
    output = {}
    raw_output = importlib.import_module('reports.' + module).main(w)
    # Fixup for varied report output formats (TBD; will push into reports once stable)
    if isinstance(raw_output, list):
      for lang, contents in raw_output:
        page = Page(w, f'{root}/{name}/{lang}')
        output[page] = contents
    else:
      page = Page(w, f'{root}/{name}')
      output[page] = raw_output
    return output
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
  # 'incorrect_redirects': 'Mistranslated redirects', # Disabled 2026-04-27 due to timeouts
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
  'bad_tags': 'Misused template tags',
  'displaytitles': 'Duplicate displaytitles',
  'duplicate_files': 'Duplicate files',
  'edit_stats': 'Users by edit count',
  'external_links2': 'External links',
  'mismatched': 'Mismatched parenthesis',
  'undocumented_templates': 'Undocumented templates',
  'unlicensed_images': 'Unlicensed images',
  'unused_files': 'Unused files',
  'wrong_date': 'Incorrect patch dates',
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

    for i, key in enumerate(monthly_reports.keys()):
      if datetime.now(timezone.utc).day == i + 1:
        modules_to_run.append(key)

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
    modules_to_run = argv[1:] if len(argv) > 1 else all_reports.keys()

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

  print('Successfully logged in, scanning page timestamps to invalidate the caches')
  w.populate_touched_cache()

  # I am working on a caching story, but it's not 100% ready yet.
  # Until then, shuffle the order of reports to guarantee a more even coverage,
  # when reports time out.
  modules_to_run = list(modules_to_run)
  shuffle(modules_to_run)
  print(f'Running reports: {modules_to_run}')

  report_start = datetime.now(timezone.utc)
  total_pipeline_duration = timedelta(hours=5, minutes=55)
  report_end = report_start + total_pipeline_duration

  sleep_before_upload = timedelta(minutes=15) # Helps avoid throttling / wiki database issues, I think
  upload_duration_guess = timedelta(minutes=15)
  report_stop = report_end - upload_duration_guess - sleep_before_upload

  # This value (on the global wiki class) acts as a soft stop for our reports,
  # so they are unable to make network requests after this time.
  w.last_network_request_time = report_stop

  comment_with_placeholders = 'Please verify the following diffs:\n'
  action_url = 'https://github.com/' + environ['GITHUB_REPOSITORY'] + '/actions/runs/' + environ['GITHUB_RUN_ID']

  all_reports_succeeded = True
  report_outputs = {}
  for module in modules_to_run:
    report_name = all_reports[module]
    output = run_report(w, module, report_name)
    if not output:
      comment_with_placeholders += f'- [ ] Report {report_name} threw an exception. Please check the [action logs]({action_url}).\n'
      all_reports_succeeded = False
      continue
    report_outputs.update(output) # Dictionary merge; includes all pages + contents

    comment_with_placeholders += f'- [ ] Report {report_name} succeeded, diffs:'
    for page in output:
      comment_with_placeholders += f' %{page.url_title}%'

    comment_with_placeholders += '\n'

  print('All reports completed, sleeping then uploading outputs')
  sleep(sleep_before_upload.total_seconds())

  w.last_network_request_time = None # Unblock network requests so we can POST again.
  w.MAX_RETRIES = 1 # We will be retrying via outer loop.


  for i in range(5):
    print(f'Still have {len(report_outputs)} pages to edit on attempt {i+1}/5')
    for page in list(report_outputs.keys()):
      contents = report_outputs[page]
      wiki_diff_url = page.edit(contents, bot=True, summary=summary)
      if wiki_diff_url:
        comment_with_placeholders = comment_with_placeholders.replace(f'%{page.url_title}%', f'[{page.lang}]({wiki_diff_url})')
        report_outputs.pop(page)

    for page in w.get_user_contribs(w.get_current_user(), report_start):
      if page not in report_outputs:
        print(f'Found unrelated edit to page {page.url_title} which was not an expected report. Not removing from the pending list.')
        continue

      wiki_diff_url = f'{page.wiki.wiki_url}?diff={page.raw["revid"]}'
      comment_with_placeholders = comment_with_placeholders.replace(f'%{page.url_title}%', f'[{page.lang}]({wiki_diff_url})')

    if len(report_outputs) == 0:
      break

  # Tried 5 times, give up on anything not uploaded
  for page, contents in report_outputs.items():
    comment_with_placeholders = comment_with_placeholders.replace(f'%{page.url_title}%', f'~~[{page.lang}]({action_url})~~')
    all_reports_succeeded = False

    # Save the contents to a file (will be attached as a build artifact)
    file_name = f'reports/wiki_{page.url_title}.txt'
    with open(file_name, 'w', encoding='utf-8') as f:
      f.write(contents)

  comment = comment_with_placeholders

  if event == 'pull_request':
    open_pr_comment.create_pr_comment(comment)
  elif event == 'workflow_dispatch':
    open_pr_comment.create_issue('Workflow dispatch finished', comment)
  elif environ['GITHUB_EVENT_NAME'] == 'schedule':
    print(comment)

  exit(0 if all_reports_succeeded else 1)

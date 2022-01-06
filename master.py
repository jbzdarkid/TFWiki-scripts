from datetime import datetime
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
# Improve the wikitools/wiki get_with_continue to actually yield the pagenames, not just the json objects.

with open(environ['GITHUB_ENV'], 'a') as f:
  subcomment = """\
Please verify the following diffs:
- [ ] foo: [en](https://wiki.tf/d/3106540) [ar](https://wiki.tf/d/3106518) [cs](https://wiki.tf/d/3106519) [da](https://wiki.tf/d/3106520) [de](https://wiki.tf/d/3106521) [es](https://wiki.tf/d/3106522) [fi](https://wiki.tf/d/3106523) [fr](https://wiki.tf/d/3106524) [hu](https://wiki.tf/d/3106525) [it](https://wiki.tf/d/3106526) [ja](https://wiki.tf/d/3106527) [ko](https://wiki.tf/d/3106528) [nl](https://wiki.tf/d/3106529) [no](https://wiki.tf/d/3106530) [pl](https://wiki.tf/d/3106531) [pt](https://wiki.tf/d/3106532) [pt-br](https://wiki.tf/d/3106533) [ro](https://wiki.tf/d/3106534) [ru](https://wiki.tf/d/3106535) [sv](https://wiki.tf/d/3106536) [tr](https://wiki.tf/d/3106537) [zh-hans](https://wiki.tf/d/3106538) [zh-hant](https://wiki.tf/d/3106539)
- [ ] bar: [en](https://wiki.tf/d/3106541)"""
  f.write('GITHUB_COMMENT<<EOF')
  f.write(subcomment)
  f.write('EOF')
with open(environ['GITHUB_ENV'], 'a') as f:
  subcomment = """\
Please verify the following diffs:
- [ ] All articles ran in 0:00:56.697371: [en](https://wiki.tf/d/3106540) [ar](https://wiki.tf/d/3106518) [cs](https://wiki.tf/d/3106519) [da](https://wiki.tf/d/3106520) [de](https://wiki.tf/d/3106521) [es](https://wiki.tf/d/3106522) [fi](https://wiki.tf/d/3106523) [fr](https://wiki.tf/d/3106524) [hu](https://wiki.tf/d/3106525) [it](https://wiki.tf/d/3106526) [ja](https://wiki.tf/d/3106527) [ko](https://wiki.tf/d/3106528) [nl](https://wiki.tf/d/3106529) [no](https://wiki.tf/d/3106530) [pl](https://wiki.tf/d/3106531) [pt](https://wiki.tf/d/3106532) [pt-br](https://wiki.tf/d/3106533) [ro](https://wiki.tf/d/3106534) [ru](https://wiki.tf/d/3106535) [sv](https://wiki.tf/d/3106536) [tr](https://wiki.tf/d/3106537) [zh-hans](https://wiki.tf/d/3106538) [zh-hant](https://wiki.tf/d/3106539)
- [ ] Wanted templates ran in 0:00:37.264911: [en](https://wiki.tf/d/3106541)"""
  print('<28>')
  f.write('GITHUB_COMMENT2<<EOF')
  f.write(subcomment)
  f.write('EOF')
print('<33>')

exit(0)

diff_links = []

def publish_single_report(w, module, report_name):
  start = datetime.now()
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

  if is_daily: # Multi-language reports need frequent updates since we have many translators
    #failures += publish_lang_report(w, 'untranslated_templates', 'Untranslated templates')
    #failures += publish_lang_report(w, 'missing_translations', 'Missing translations')
    #failures += publish_lang_report(w, 'missing_categories', 'Untranslated categories')
    failures += publish_lang_report(w, 'all_articles', 'All articles')

  if is_weekly: # English (or cross-language) reports which are not too costly to run
    failures += publish_single_report(w, 'wanted_templates', 'Wanted templates')
    #failures += publish_single_report(w, 'navboxes', 'Pages which are missing navboxes')
    #failures += publish_single_report(w, 'overtranslated', 'Pages with no english equivalent')
    #failures += publish_single_report(w, 'incorrectly_categorized', 'Pages with incorrect categorization')
    #failures += publish_single_report(w, 'undocumented_templates', 'Undocumented templates')

  if is_monthly: # Expensive or otherwise infrequently-changing reports
    failures += publish_single_report(w, 'duplicate_files', 'Duplicate files')
    failures += publish_single_report(w, 'unused_files', 'Unused files')
    failures += publish_single_report(w, 'edit_stats', 'Users by edit count')
    failures += publish_single_report(w, 'external_links', 'External links')
    failures += publish_single_report(w, 'mismatched', 'Mismatched parenthesis')

  def add_diff_link(report, language, link):
    if report not in diff_links:
      diff_links[report] = f'- [ ] {report}:'
    diff_links[report][language] = link

  comment = 'Please verify the following diffs:\n'
  for report_name, duration, link_map in diff_links:
    comment += f'- [ ] {report_name} ran in {duration}:'
    languages = sorted(link_map.keys(), key=lambda lang: (lang != 'en', lang)) # Sort languages, keeping english first
    for language in languages:
      comment += f' [{language}]({link_map[language]})'
    comment += '\n'

  # Pass this as output to github-actions, so it can be used in later steps
  with open(environ['GITHUB_ENV'], 'a') as f:
    subcomment = """\
[a](foo)
[b](bar)"""
    f.write('GITHUB_COMMENT<<EOF')
    f.write(subcomment)
    f.write('EOF')
    subcomment = """\
[a](https://wiki.tf/d/12345)
[b](https://wiki.tf/d/12345)"""
    f.write('GITHUB_COMMENT<<EOF')
    f.write(subcomment)
    f.write('EOF')
    subcomment = """\
- [ ] [a](https://wiki.tf/d/12345)
- [ ] [b](https://wiki.tf/d/12345)"""
    f.write('GITHUB_COMMENT<<EOF')
    f.write(subcomment)
    f.write('EOF')
    for i in range(len(comment)):
      subcomment = comment[:i]
      print(f'\n{i}:\n{subcomment}\n')
      f.write('GITHUB_COMMENT<<EOF')
      f.write(subcomment)
      f.write('EOF')

  exit(failures)

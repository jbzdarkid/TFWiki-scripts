from datetime import datetime
from os import environ
from sys import argv
from wikitools import wiki

# I remember writing a script (no idea where it went) to check for mismatched braces/brackets on article pages.
# I need to decide what to do about some of the reports on TFW:Reports which seem useless. I should also check history; I think I cut some of these a while ago.
# I would like to write a script which scrapes Special:WantedTemplates to check for Templates which are used in (Main).

if argv[0] == 'test':
  root = 'User:Darkid/Reports'
  is_daily = True
  is_weekly = True
  is_monthly = True
  summary = 'Test update via https://github.com/jbzdarkid/TFWiki-scripts'
else:
  root = 'Team Fortress Wiki:Reports'
  is_daily = True
  is_weekly = datetime.now().weekday() == 0 # Monday
  is_monthly = datetime.now().day == 1 # 1st of every month
  summary = 'Automatic update via https://github.com/jbzdarkid/TFWiki-scripts'

w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
if not w.login(environ['WIKI_USERNAME'], environ['WIKI_PASSWORD']):
  exit(1)

if is_daily:
  from untranslated_templates import main
  for lang, output in main():
    print(Page(w, f'{root}/Untranslated templates/{lang}').edit(output, bot=True, summary=summary))

  from missing_translations import main
  for lang, output in main():
    print(Page(w, f'{root}/Missing translations/{lang}').edit(output, bot=True, summary=summary))

  from all_articles import main
  for lang, output in main():
    print(Page(w, f'{root}/All articles/{lang}').edit(output, bot=True, summary=summary))

if is_daily or is_weekly:
  pass

if is_daily or is_weekly or is_monthly:
  from edit_stats import main
  print(Page(w, f'{root}/Users by edit count').edit(text=main(), bot=True, summary=summary))

  from undocumented_templates import main
  print(Page(w, f'{root}/Undocumented templates').edit(text=main(), bot=True, summary=summary))

  from unused_files import main
  print(Page(w, f'{root}/Unused files').edit(text=main(), bot=True, summary=summary))

  from external_links import main
  print(Page(w, f'{root}/External links').edit(text=main(), bot=True, summary=summary))

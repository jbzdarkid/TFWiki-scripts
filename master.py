from wikitools.page import Page
from wikitools import wiki
from os import environ

w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
if not w.login(environ['WIKI_USERNAME'], environ['WIKI_PASSWORD']):
  exit(1)

summary = 'Automatic update via https://github.com/jbzdarkid/TFWiki-scripts'

if True: # TODO: Disable testing once I think it works.
  root = 'User:Darkid/Reports'
else:
  root = 'Team Fortress Wiki:Reports'

from edit_stats import main
print(Page(w, f'{root}/Users by edit count').edit(text=main(), bot=True, summary=summary))

from undocumented_templates import main
print(Page(w, f'{root}/Undocumented templates').edit(text=main(), bot=True, summary=summary))
  
from unused_files import main
print(Page(w, f'{root}/Unused files').edit(text=main(), bot=True, summary=summary))

from untranslated_templates import main
for lang, output in main():
  print(Page(w, f'{root}/Untranslated templates/{lang}').edit(output, bot=True, summary=summary))

from missing_translations import main
for lang, output in main():
  print(Page(w, f'{root}/Missing translations/{lang}').edit(output, bot=True, summary=summary))

from all_articles import main
for lang, output in main():
  print(Page(w, f'{root}/All articles/{lang}').edit(output, bot=True, summary=summary))

from external_links import main
print(Page(w, f'{root}/External links').edit(text=main(), bot=True, summary=summary))

# I remember writing a script (no idea where it went) to check for mismatched braces/brackets on article pages.
# I need to decide what to do about some of the reports on TFW:Reports which seem useless. I should also check history; I think I cut some of these a while ago.
# I would like to write a script which scrapes Special:WantedTemplates to check for Templates which are used in (Main).

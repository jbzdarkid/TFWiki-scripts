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

import edit_stats
print(Page(w, f'{root}/Users by edit count').edit(text=edit_stats.main(), bot=True, summary=summary))

import undocumented_templates
print(Page(w, f'{root}/Undocumented templates').edit(text=undocumented_templates.main(), bot=True, summary=summary))

import untranslated_templates
for lang, output in untranslated_templates.main():
  print(Page(w, f'{root}/Untranslated templates/{lang}').edit(output, bot=True, summary=summary))
  
import unused_files
print(Page(w, f'{root}/Unused files').edit(text=unused_files.main(), bot=True, summary=summary))

import external_links
print(Page(w, f'{root}/External links').edit(text=external_links.main(), bot=True, summary=summary))

# I remember writing a script (no idea where it went) to check for mismatched braces/brackets on article pages.
# I would like to write a script which scrapes Special:WantedTemplates to check for Templates which are used in (Main).
# I would like to restore Missing translations/lang and All articles/lang.

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
outputs = untranslated_templates.main()
for lang, output in outputs:
  print(Page(w, f'{root}/Untranslated templates/{lang}').edit(output, bot=True, summary=summary))
  
import unused_files
print(Page(w, f'{root}/Unused files').edit(text=unused_files.main(), bot=True, summary=summary))

#import external_links
#print(Page(w, f'{root}/External links').edit(text=external_links.main(), bot=True, summary=summary))

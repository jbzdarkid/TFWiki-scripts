from wikitools.page import Page
from wikitools import wiki
from os import environ

# travis encrypt WIKI_USERNAME=pootis -a -x
# travis encrypt WIKI_PASSWORD=woooki -a -p

w = wiki.Wiki('http://wiki.teamfortress.com/w/api.php')
w.login(environ['WIKI_USERNAME'], environ['WIKI_PASSWORD'])

summary = 'Automatic update using Travis-ci and https://github.com/jbzdarkid/TFWiki-scripts'

import edit_stats
print Page(w, 'Team Fortress Wiki:Reports/Users by edit count').edit(text=edit_stats.main(), bot=True, summary=summary)

import external_links
verbose=True
print Page(w, 'Team Fortress Wiki:Reports/External links').edit(text=external_links.main(), bot=True, summary=summary)
verbose=False

import undocumented_templates
print Page(w, 'Team Fortress Wiki:Reports/Undocumented templates').edit(text=undocumented_templates.main(), bot=True, summary=summary)

import untranslated_templates
outputs = untranslated_templates.main()
for lang, output in outputs:
  print Page(w, 'Team Fortress Wiki:Reports/Untranslated templates/%s' % lang).edit(output, bot=True, summary=summary)
  
  import unused_files
print Page(w, 'Team Fortress Wiki:Reports/Unused files').edit(text=unused_files.main(), bot=True, summary=summary)

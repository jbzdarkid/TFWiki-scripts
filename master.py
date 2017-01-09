from wikitools.page import Page
from wikitools import wiki
from os import environ

# travis encrypt WIKI_USERNAME=pootis -a -x
# travis encrypt WIKI_PASSWORD=woooki -a -p

w = wiki.Wiki('http://wiki.teamfortress.com/w/api.php')
w.login(environ['WIKI_USERNAME'], environ['WIKI_PASSWORD'])

summary = 'Automatic update using Travis-ci and https://github.com/jbzdarkid/TFWiki-scripts'

import wiki_edit_stats
Page(w, 'Team Fortress Wiki:Reports/Users by edit count').edit(text=wiki_edit_stats.main(), summary=summary)

import wiki_undocumented_templates
Page(w, 'Team Fortress Wiki:Reports/Undocumented templates').edit(text=wiki_undocumented_templates.main(), summary=summary)

import wiki_unused_files
Page(w, 'Team Fortress Wiki:Reports/Unused files').edit(text=wiki_unused_files.main(), summary=summary)

# import equipregions
# text = Page(w, 'Template:Equip region table').getWikiText()
# start = text.index('! {{item name|') # Start of equip regions
# end = text.index('<noinclude>') # End of table
# Page(w, 'Template:Equip region table').edit(text=text[:start]+equipregions.main()+text[end:], summary=summary)

# import LODTables
# Page(w, 'Template:LODTable').edit(text=LODTables.main(), summary=summary)

import external_links_analyse2
Page(w, 'Team Fortress Wiki:Reports/External links').edit(text=external_links_analyse2.main(), summary=summary)

import wiki_untranslated_templates
outputs = wiki_untranslated_templates.main()
for lang, output in outputs:
  Page(w, 'Team Fortress Wiki:Reports/Untranslated templates/%s' % lang).edit(output, summary=summary)
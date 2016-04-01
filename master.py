from wikitools.page import Page
from wikitools import wiki
import config
w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')

w = wiki.Wiki(config['wikiApi'])
w.login(config['wikiUsername'], config['wikiPassword'])

summary = 'Automatic Update by %s using [https://github.com/jbzdarkid/TFWiki-scripts Wikitools]' % config['wikiUsername']

import wiki_edit_stats, wiki_undocumented_templates, wiki_unused_files, equipregions, external_links_analyse2, LODTables

Page(w, 'Team Fortress Wiki:Reports/Users by edit count').edit(text=wiki_edit_stats.main(), summary=summary)

Page(w, 'Team Fortress Wiki:Reports/Undocumented templates').edit(text=wiki_undocumented_templates.main(), summary=summary)

Page(w, 'Team Fortress Wiki:Reports/Unused files').edit(text=wiki_unused_files.main(), summary=summary)

text = Page(w, 'Template:Equip region table').getWikiText()
start = text.index('! {{item name|') # Start of equip regions
end = text.index('<noinclude>') # End of table
Page(w, 'Template:Equip region table').edit(text=text[:start]+equipregions.main()+text[end:], summary=summary)

Page(w, 'Template:LODTable').edit(text=LODTables.main(), summary=summary)

Page(w, 'Team Fortress Wiki:Reports/External links').edit(text=external_links_analyse2.main(), summary=summary)

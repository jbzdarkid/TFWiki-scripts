from wikitools.page import Page
from wikitools import wiki
w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
username = raw_input('Username: ')
w.login(username)

summary = 'Automatic Update by %s using [https://github.com/jbzdarkid/TFWiki-scripts Wikitools]' % username

import wiki_edit_stats, wiki_unused_files, equipregions, external_links_analyse


'''
Page(w, 'Team Fortress Wiki:Reports/Users by edit count').edit(text=wiki_edit_stats.main(), summary=summary)
p
'''
Page(w, 'Team Fortress Wiki:Reports/Unused files').edit(text=wiki_unused_files.main(), summary=summary)


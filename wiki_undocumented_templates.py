from urllib2 import urlopen, quote
from json import loads
from Queue import Queue, Empty
from threading import Thread
from wikitools import wiki
from wikitools.page import Page
from re import search, sub

verbose = False
PAGESCRAPERS = 10

def allpages(page_q):
	wikiAddress = r'http://wiki.teamfortress.com/w/api.php?action=query&list=allpages&apfilterredir=nonredirects&apnamespace=10&aplimit=500&format=json' # Namespace 10 is Templates
	url = wikiAddress
	while True:
		result = loads(urlopen(url.encode('utf-8')).read())
		for page in result['query']['allpages']:
			if '/' in page['title']:
				continue # Don't include subpages
			elif page['title'].partition('/')[0] == 'Template:Dictionary':
				continue # Don't include dictionary subpages
			elif page['title'].partition('/')[0] == 'Template:PatchDiff':
				continue # Don't include patch diffs.
			elif page['title'][:13] == 'Template:User':
				continue # Don't include userboxes.
			page_q.put(page['title'])
		if 'continue' not in result:
			break
		url = wikiAddress + '&apcontinue=' + result['continue']['apcontinue']
	wikiAddress = r'http://wiki.teamfortress.com/w/api.php?action=query&list=allpages&apfilterredir=nonredirects&apnamespace=828&aplimit=500&format=json' # Namespace 828 is Modules
	url = wikiAddress
	while True:
		result = loads(urlopen(url.encode('utf-8')).read())
		for page in result['query']['allpages']:
			if '/' in page['title']:
				continue # Don't include subpages
			elif page['title'].partition('/')[0] == 'Template:Dictionary':
				continue # Don't include dictionary subpages
			elif page['title'].partition('/')[0] == 'Template:PatchDiff':
				continue # Don't include patch diffs.
			elif page['title'][:13] == 'Template:User':
				continue # Don't include userboxes.
			page_q.put(page['title'])
		if 'continue' not in result:
			global stage
			stage = 1
			return
		url = wikiAddress + '&apcontinue=' + result['continue']['apcontinue']

def whatlinkshere(page):
	url = r'http://wiki.teamfortress.com/w/api.php?action=query&list=embeddedin&eifilterredir=nonredirects&eititle=%s&eilimit=500&format=json' % quote(page.encode('utf-8'))
	result = loads(urlopen(url.encode('utf-8')).read())
	if 'continue' not in result:
		return len(result['query']['embeddedin'])
	else:
		return 1000

def pagescraper(page_q, badpages):
	w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
	while True:
		try:
			page = page_q.get(True, 1)
		except Empty:
			global stage
			if stage > 0: # This is still not totally thread-safe.
				stage += 1
				return
			else:
				continue

		page_text = Page(w, page).getWikiText()
		page_visible = sub('<includeonly>.*?</includeonly>', '', page_text)
		if len(page_text) - len(page_visible) < 150:
			continue # Pages that don't hide much of their information, e.g. nav templates
		else:
			print page, 'hides', len(page_text) - len(page_visible), 'characters'

		match = search('{{([Dd]oc begin|[Tt]emplate doc|[Dd]ocumentation|[Ww]ikipedia doc)}}', page_text)
		if not match:
			count = whatlinkshere(page)
			print 'Page %s does not transclude a documentation template and has %d backlinks' % (page, count)
			badpages.append([count, page])

def main():
	global stage
	stage = 0
	threads = []
	# Stage 0: Generate list of pages
	page_q = Queue()
	thread = Thread(target=allpages, args=(page_q,)) # args must be a tuple, (page_q) is not a tuple.
	threads.append(thread)
	thread.start()
	# Stage 1: All pages generated. Pagescrapers are allowed to exit if Page Queue is empty.
	badpages = []
	for i in range(PAGESCRAPERS): # Number of threads
		thread = Thread(target=pagescraper, args=(page_q, badpages))
		threads.append(thread)
		thread.start()
	for thread in threads:
		thread.join()

	badpages.sort(key=lambda s: (1000-s[0], s[1]))
	output = '{{DISPLAYTITLE:%d templates without documentation}}\n' % len(badpages)
	for page in badpages:
		output += '* [[%s|]] ([{{fullurl:Special:WhatLinksHere/%s|limit=%d}} %s use%s])\n' % (page[1], page[1], page[0], str(page[0]) if page[0] < 500 else '500+', '' if page[0] == 1 else 's')
	return output.encode('utf-8')

if __name__ == '__main__':
	verbose = True
	f = open('wiki_undocumented_templates.txt', 'wb')
	f.write(main())
	print 'Article written to wiki_undocumented_templates.txt'
	f.close()
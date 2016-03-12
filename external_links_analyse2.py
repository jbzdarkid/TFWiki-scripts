from json import loads
from Queue import Queue, Empty
from re import compile, DOTALL
from socket import timeout, gaierror
from threading import Thread
from urllib2 import urlopen, build_opener, HTTPError, URLError
from wikitools import wiki
from wikitools.page import Page
verbose = False
PAGESCRAPERS = 1
LINKCHECKERS = 1

# Shamelessly copied from the old external_links_analyse.
def return_link_regex(withoutBracketed=False, onlyBracketed=False):
	"""Return a regex that matches external links."""
	# RFC 2396 says that URLs may only contain certain characters.
	# For this regex we also accept non-allowed characters, so that the bot
	# will later show these links as broken ('Non-ASCII Characters in URL').
	# Note: While allowing dots inside URLs, MediaWiki will regard
	# dots at the end of the URL as not part of that URL.
	# The same applies to comma, colon and some other characters.
	notAtEnd = '\]\s\.:;,<>"\|)'
	# So characters inside the URL can be anything except whitespace,
	# closing squared brackets, quotation marks, greater than and less
	# than, and the last character also can't be parenthesis or another
	# character disallowed by MediaWiki.
	notInside = '\]\s<>"'
	# The first half of this regular expression is required because '' is
	# not allowed inside links. For example, in this wiki text:
	#	   ''Please see http://www.example.org.''
	# .'' shouldn't be considered as part of the link.
	regex = r'(?P<url>http[s]?://[^' + notInside + ']*?[^' + notAtEnd \
		+ '](?=[' + notAtEnd+ ']*\'\')|http[s]?://[^' + notInside \
		+ ']*[^' + notAtEnd + '])'

	if withoutBracketed:
		regex = r'(?<!\[)' + regex
	elif onlyBracketed:
		regex = r'\[' + regex
	return compile(regex)

# Also shamelessly copied from the old external_links_analyse.
def get_links(regex, text):
	nestedTemplateR = compile(r'{{([^}]*?){{(.*?)}}(.*?)}}')
	while nestedTemplateR.search(text):
		text = nestedTemplateR.sub(r'{{\1 \2 \3}}', text)

	# Then blow up the templates with spaces so that the | and }} will not be regarded as part of the link:.
	templateWithParamsR = compile(r'{{([^}]*?[^ ])\|([^ ][^}]*?)}}', DOTALL)
	while templateWithParamsR.search(text):
		text = templateWithParamsR.sub(r'{{ \1 | \2 }}', text)

	for m in regex.finditer(text):
		yield m.group('url')

# End of stuff I shamelessly copied.

def allpages(page_q):
	wikiAddress = r'https://wiki.teamfortress.com/w/api.php?action=query&list=allpages&apfilterredir=nonredirects&aplimit=500&format=json'
	url = wikiAddress
	langs = ['ar', 'cs', 'da', 'de', 'es', 'fi' ,'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']
	while True:
		result = loads(urlopen(url.encode('utf-8')).read())
		for page in result['query']['allpages']:
			if page['title'].rpartition('/')[2] in langs:
				continue # English pages only
		if 'continue' not in result:
			page_q.put(page['title'])
			global stage
			stage = 1
			return
		url = wikiAddress + '&apcontinue=' + result['continue']['apcontinue']

def pagescraper(page_q, link_q, links):
	w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
	while True:
		try:
			page = page_q.get(True, 1)
		except Empty:
			global stage
			if stage > 0: # This is still not totally thread-safe.
				stage += 1
				print 'Pagescraper exiting, stage:', stage
				return
			else:
				print 'Pagescraper continuing <81>'
				continue

		# if verbose:
		# 	print 'Getting links from', page

		content = Page(w, page).getWikiText()
		linkRegex = return_link_regex()
		for url in get_links(linkRegex, content):
			if url not in links:
				links[url] = []
				link_q.put(url)
			if page not in links[url]:
				links[url].append(page)

def linkchecker(links_q, linkData):
	while True:
		try:
			link = links_q.get(True, 1)
		except Empty:
			global stage
			if stage > PAGESCRAPERS: # This is still not totally thread-safe.
				stage += 1
				print 'Linkscraper exiting, stage:', stage
				return
			else:
				print 'Linkscraper continuing <103>'
				continue

		# if verbose:
			# print 'Processing', link
		try:
			opener = build_opener()
			opener.addheaders.append(('Cookie', 'viewed_welcome_page=1')) # For ESEA, to prevent a redirect loop.
			opener.open(link, timeout=5).read() # Timeout is in seconds
			continue # No error
		except timeout as e:
			linkData.append(('Timeout', link))
		except HTTPError as e:
			if e.code == 404:
				linkData.append(('Not Found', link))
			elif e.code == 403:
				linkData.append(('Not Permitted', link))
			elif e.code == 503:
				linkData.append(('Internal Server Error', link))
			else:
				print 1, e.code, e
				linkData.append((e.reason, link))
		except URLError as e:
			if isinstance(e.reason, timeout):
				linkData.append(('Timeout', link))
			elif isinstance(e.reason, gaierror):
				linkData.append(('Unknown Host', link))
			else:
				print 2, e.args
				linkData.append((e.reason, link))
		except Exception as e:
			raise e
		# if verbose:
		# 	print 'Found dead link:', link

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
	links = {}
	link_q = Queue()
	for i in range(PAGESCRAPERS): # Number of threads
		thread = Thread(target=pagescraper, args=(page_q, link_q, links))
		threads.append(thread)
		thread.start()
	# Stage 2: All pages scraped. Linkscrapers are allowed to exit if Link Queue is empty.
	linkData = []
	for i in range(LINKCHECKERS): # Number of threads
		thread = Thread(target=linkchecker, args=(link_q, linkData))
		threads.append(thread)
		thread.start()
	for thread in threads:
		thread.join()

	output = ''
	linkData.sort()
	lastError = ''
	for error, link in linkData:
		if lastError != error:
			lastError = error
			output += '== %s ==\n' % lastError
		output += '=== [%s] ===\n' % link
		for page in sorted(links[link]):
			output += '* [[%s]]\n' % page

	return output

if __name__ == '__main__':
	verbose = True
	f = open('external_links_analyse.txt', 'wb')
	f.write(main())
	print 'Article written to external_links_analyse.txt'
	f.close()
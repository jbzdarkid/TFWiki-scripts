from json import loads
from Queue import Queue, Empty
from re import compile, DOTALL
from socket import timeout, gaierror
from threading import Thread
from urllib2 import urlopen, build_opener, HTTPError, URLError
from wikitools import wiki
from wikitools.page import Page
verbose = False

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

def get_all_pages():
	wikiAddress = r'https://wiki.teamfortress.com/w/api.php?action=query&list=allpages&apfilterredir=nonredirects&aplimit=500&format=json'
	url = wikiAddress
	langs = ['ar', 'cs', 'da', 'de', 'es', 'fi' ,'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']
	while True:
		result = loads(urlopen(url.encode('utf-8')).read())
		for page in result['query']['allpages']:
			if page['title'].rpartition('/')[2] in langs:
				continue # English pages only
			yield page['title']
		if 'continue' not in result:
			return
		return ###
		url = wikiAddress + '&apcontinue=' + result['continue']['apcontinue']

def generate_links(q, links):
	w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
	for page in get_all_pages():
		content = Page(w, page).getWikiText()
		linkRegex = return_link_regex()
		for url in get_links(linkRegex, content):
			if url not in links:
				links[url] = []
				q.put(url)
			if page not in links[url]:
				links[url].append(page)

	return links

def worker(q, linkData):
	firstLink = True
	while True:
		try:
			link = q.get(True, 10 if firstLink else 1)
			firstLink = False
		except Empty:
			return

		if verbose:
			print 'Processing', link
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
		if verbose:
			print 'Found dead link:', link

def main():
	q = Queue()
	links = {}
	linkData = []
	threads = []

	thread = Thread(target=generate_links, args=(q, links))
	threads.append(thread)
	thread.start()
	for i in range(50): # Number of threads
		thread = Thread(target=worker, args=(q, linkData))
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
		output += '=== %s ===\n' % link
		for page in sorted(links[link]):
			output += '* [[%s]]\n' % page

	return output

if __name__ == '__main__':
	verbose = True
	f = open('external_links_analyse.txt', 'wb')
	f.write(main())
	print 'Article written to external_links_analyse.txt'
	f.close()
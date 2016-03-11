from json import loads
from Queue import Queue, Empty
from re import compile, DOTALL
from threading import Thread
from urllib import quote
from urllib2 import urlopen
from urlparse import urlsplit
from wikitools.page import Page
from wikitools import wiki
import httplib, socket # Only imported for errors?

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

# There's probably (hopefully) a cleaner way of verifying links than this... but until then, I've copied this from the old external_links_analyse.
class LinkChecker(object):
	'''
	Given a HTTP URL, tries to load the page from the Internet and checks if it
	is still online.

	Returns a (boolean, string) tuple saying if the page is online and including
	a status reason.

	Warning: Also returns false if your Internet connection isn't working
	correctly! (This will give a Socket Error)
	'''
	def __init__(self, url, redirectChain = [], serverEncoding=None, HTTPignore=[]):
		"""
		redirectChain is a list of redirects which were resolved by
		resolve_redirect(). This is needed to detect redirect loops.
		"""
		self.url = url
		self.serverEncoding = serverEncoding
		self.header = {
			'User-agent': 'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.8) Gecko/20051128 SUSE/1.5-0.1 Firefox/1.5',
			'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
			'Accept-Language': 'de-de,de;q=0.8,en-us;q=0.5,en;q=0.3',
			'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
			'Keep-Alive': '30',
			'Connection': 'keep-alive',
		}
		self.redirectChain = redirectChain + [url]
		self.change_url(url)
		self.HTTPignore = HTTPignore

	def get_connection(self):
		if self.scheme == 'http':
			return httplib.HTTPConnection(self.host, timeout=30)
		elif self.scheme == 'https':
			return httplib.HTTPSConnection(self.host, timeout=30)

	def get_encoding_used_by_server(self):
		if not self.serverEncoding:
			try:
				print(u'Contacting server %s to find out its default encoding...' % self.host)
				conn = self.get_connection()
				conn.request('HEAD', '/', None, self.header)
				self.response = conn.getresponse()

				self.read_encoding_from_response(self.response)
			except:
				pass
			if not self.serverEncoding:
				# TODO: We might also load a page, then check for an encoding
				# definition in a HTML meta tag.
				print(u'Error retrieving server\'s default charset. Using ISO 8859-1.')
				# most browsers use ISO 8859-1 (Latin-1) as the default.
				self.serverEncoding = 'iso8859-1'
		return self.serverEncoding

	def read_encoding_from_response(self, response):
		if not self.serverEncoding:
			try:
				ct = response.getheader('Content-Type')
				charsetR = compile('charset=(.+)')
				charset = charsetR.search(ct).group(1)
				self.serverEncoding = charset
			except:
				pass

	def change_url(self, url):
		self.url = url
		# we ignore the fragment
		self.scheme, self.host, self.path, self.query, self.fragment = urlsplit(self.url)
		if not self.path:
			self.path = '/'
		if self.query:
			self.query = '?' + self.query
		self.protocol = url.split(':', 1)[0]
		# check if there are non-ASCII characters inside path or query, and if
		# so, encode them in an encoding that hopefully is the right one.
		try:
			self.path.encode('ascii')
			self.query.encode('ascii')
		except UnicodeEncodeError:
			encoding = self.get_encoding_used_by_server()
			self.path = unicode(quote(self.path.encode(encoding)))
			self.query = unicode(quote(self.query.encode(encoding), '=&'))

	def resolve_redirect(self, useHEAD = False):
		'''
		Requests the header from the server. If the page is an HTTP redirect,
		returns the redirect target URL as a string. Otherwise returns None.

		If useHEAD is true, uses the HTTP HEAD method, which saves bandwidth
		by not downloading the body. Otherwise, the HTTP GET method is used.
		'''
		conn = self.get_connection()
		try:
			if useHEAD:
				conn.request('HEAD', '%s%s' % (self.path, self.query), None,
							 self.header)
			else:
				conn.request('GET', '%s%s' % (self.path, self.query), None,
							 self.header)
			self.response = conn.getresponse()
			# read the server's encoding, in case we need it later
			self.read_encoding_from_response(self.response)
		except httplib.BadStatusLine:
			# Some servers don't seem to handle HEAD requests properly,
			# e.g. http://www.radiorus.ru/ which is running on a very old
			# Apache server. Using GET instead works on these (but it uses
			# more bandwidth).
			if useHEAD:
				return self.resolve_redirect(useHEAD = False)
			else:
				raise
		if self.response.status >= 300 and self.response.status <= 399:
			#print response.getheaders()
			redirTarget = self.response.getheader('Location')
			if redirTarget:
				try:
					redirTarget.encode('ascii')
				except UnicodeError:
					redirTarget = redirTarget.decode(
						self.get_encoding_used_by_server())
				if redirTarget.startswith('http://') or \
					 redirTarget.startswith('https://'):
					self.change_url(redirTarget)
					return True
				elif redirTarget.startswith('/'):
					self.change_url(u'%s://%s%s'
									 % (self.protocol, self.host, redirTarget))
					return True
				else: # redirect to relative position
					# cut off filename
					directory = self.path[:self.path.rindex('/') + 1]
					# handle redirect to parent directory
					while redirTarget.startswith('../'):
						redirTarget = redirTarget[3:]
						# some servers redirect to .. although we are already
						# in the root directory; ignore this.
						if directory != '/':
							# change /foo/bar/ to /foo/
							directory = directory[:-1]
							directory = directory[:directory.rindex('/') + 1]
					self.change_url('%s://%s%s%s'
									 % (self.protocol, self.host, directory,
										redirTarget))
					return True
		else:
			return False # not a redirect

	def check(self, useHEAD = False):
		"""
		Returns True and the server status message if the page is alive.
		Otherwise returns false
		"""
		try:
			wasRedirected = self.resolve_redirect(useHEAD = useHEAD)
		except UnicodeError, error:
			return False, u'Encoding Error: %s (%s)' \
					 % (error.__class__.__name__, unicode(error))
		except httplib.error, error:
			return False, u'HTTP Error: %s' % error.__class__.__name__
		except socket.error, error:
			# http://docs.python.org/lib/module-socket.html :
			# socket.error :
			# The accompanying value is either a string telling what went
			# wrong or a pair (errno, string) representing an error
			# returned by a system call, similar to the value
			# accompanying os.error
			if isinstance(error, basestring):
				msg = error
			else:
				try:
					msg = error[1]
				except IndexError:
					print u'### DEBUG information for #2972249'
					raise IndexError, type(error)
			# TODO: decode msg. On Linux, it's encoded in UTF-8.
			# How is it encoded in Windows? Or can we somehow just
			# get the English message?
			return False, u'Socket Error: %s' % repr(msg)
		if wasRedirected:
			if self.url in self.redirectChain:
				if useHEAD:
					# Some servers don't seem to handle HEAD requests properly,
					# which leads to a cyclic list of redirects.
					# We simply start from the beginning, but this time,
					# we don't use HEAD, but GET requests.
					redirChecker = LinkChecker(self.redirectChain[0],
												 serverEncoding=self.serverEncoding,
												 HTTPignore=self.HTTPignore)
					return redirChecker.check(useHEAD = False)
				else:
					urlList = ['[%s]' % url for url in self.redirectChain + [self.url]]
					return False, u'HTTP Redirect Loop: %s' % ' -> '.join(urlList)
			elif len(self.redirectChain) >= 19:
				if useHEAD:
					# Some servers don't seem to handle HEAD requests properly,
					# which leads to a long (or infinite) list of redirects.
					# We simply start from the beginning, but this time,
					# we don't use HEAD, but GET requests.
					redirChecker = LinkChecker(self.redirectChain[0],
												 serverEncoding=self.serverEncoding,
												 HTTPignore = self.HTTPignore)
					return redirChecker.check(useHEAD = False)
				else:
					urlList = ['[%s]' % url for url in self.redirectChain + [self.url]]
					return False, u'Long Chain of Redirects: %s' % ' -> '.join(urlList)
			else:
				redirChecker = LinkChecker(self.url, self.redirectChain,
											 self.serverEncoding,
											 HTTPignore=self.HTTPignore)
				return redirChecker.check(useHEAD = useHEAD)
		else:
			try:
				conn = self.get_connection()
			except httplib.error, error:
				return False, u'HTTP Error: %s' % error.__class__.__name__
			try:
				conn.request('GET', '%s%s'
							 % (self.path, self.query), None, self.header)
			except socket.error, error:
				return False, u'Socket Error: %s' % repr(error[1])
			try:
				self.response = conn.getresponse()
			except Exception, error:
				return False, u'Error: %s' % error
			# read the server's encoding, in case we need it later
			self.read_encoding_from_response(self.response)
			# site down if the server status is between 400 and 499
			alive = self.response.status not in range(400, 500)
			if self.response.status in self.HTTPignore:
				alive = False
			return alive, '%s %s' % (self.response.status, self.response.reason)

# End of stuff I shamelessly copied.

def get_all_pages():
	wikiAddress = r'https://wiki.teamfortress.com/w/api.php?action=query&list=allpages&apfilterredir=nonredirects&aplimit=500&format=json'
	url = wikiAddress
	while True:
		result = loads(urlopen(url.encode('utf-8')).read())
		for page in result['query']['allpages']:
			yield page
		if 'continue' not in result:
			return
		url = wikiAddress + '&apcontinue=' + result['continue']['apcontinue']

def generate_links(q):
	w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
	links = {}

	for page in get_all_pages():
		print page
		content = Page(w, page['title']).getWikiText()
		linkRegex = return_link_regex()
		for url in get_links(linkRegex, content):
			if url not in links:
				links[url] = []
			links[url].append(page)
			q.put(url)

	return links

def worker(q, linkData):
	while True:
		try:
			link = q.get(True, 1)
		except Empty:
			return

		print link

		linkData[link] = LinkChecker(link).check()
		print linkData[link]



def main():
	q = Queue()
	linkData = {}
	# threads = []
	# for i in range(1): # Number of threads
	# 	thread = Thread(target=worker, args=(q, linkData))
	# 	threads.append(thread)
	# 	thread.start()
	# for thread in threads:
	# 	thread.join()
	generate_links(q)
	worker(q, linkData)


if __name__ == '__main__':
	f = open('external_links_analyse', 'wb')
	f.write(main())
	f.close()
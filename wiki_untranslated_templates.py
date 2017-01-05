from urllib2 import urlopen, quote
from json import loads
from Queue import Queue, Empty
from threading import Thread
from wikitools import wiki
from wikitools.page import Page
from re import finditer, DOTALL
from time import gmtime, strftime

verbose = False
PAGESCRAPERS = 50

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
		return 1000 # >500

def pagescraper(page_q, translations):
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
		# First, find the matching pairs
		def get_indices(char, string):
			index = -1
			indices = []
			while 1:
				try:
					index = string.index(char, index+1)
				except ValueError:
					break
				indices.append(index)
			return indices

		locations = [[len(page_text), -1]]
		for open in get_indices('{', page_text):
			locations.append([open, 1])
		for close in get_indices('}', page_text):
			locations.append([close, -1])
		locations.sort()

		# Next, divide the text up based on those pairs. Embedded text is separated out, e.g. {a{b}c} will become "ac" and "b".
		stack = [0]
		buffer = {0: ''}
		lastIndex = 0
		for index, value in locations:
			try:
				buffer[stack[-1]] += page_text[lastIndex:index]
			except KeyError: #
				buffer[stack[-1]] = page_text[lastIndex:index]
			except IndexError: # Unmached parenthesis, e.g. Class Weapons Tables
				buffer[0] += page_text[lastIndex:index] # Add text to default layer
				stack.append(None) # So there's something to .pop()
				print 'Found a closing brace without a matched opening brace, exiting'
			if value == 1:
				stack.append(index)
			elif value == -1:
				stack.pop()
			lastIndex = index + 1

		print page, 'contains', len(buffer), 'pairs of braces'

		missing_languages = set()
		for language in translations:
			translations[language][page] = 0
		# Finally, search through for lang templates via positive lookahead
		for match in finditer('{(?=(.*?)\|)', page_text, DOTALL):
			template = match.group(1).strip().lower()
			languages = []
			if template == 'lang': # And count out their params
				if page_text[match.start()-2:match.start()+1] == '{{{':
					continue # Skip any parameters named lang, viz.: {{{lang|}}}
				for match2 in finditer('\|(.*?)=', buffer[match.start()]):
					languages.append(match2.group(1).strip().lower())
				for language in translations:
					if language not in languages: # Add missing translations
						translations[language][page] += 1
						missing_languages.add(language)
		if len(missing_languages) > 0:
			print page, 'is not translated into', len(missing_languages), 'languages:', ', '.join(missing_languages)

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
	translations = {lang: {} for lang in 'ar, cs, da, de, en, es, fi, fr, hu, it, ja, ko, nl, no, pl, pt, pt-br, ro, ru, tr, sv, zh-hans, zh-hant'.split(', ')}
	for i in range(PAGESCRAPERS): # Number of threads
		thread = Thread(target=pagescraper, args=(page_q, translations))
		threads.append(thread)
		thread.start()
	for thread in threads:
		thread.join()

	outputs = []
	for language in sorted(translations.keys()):
		output = """
{{DISPLAYTITLE: {count} templates missing {{lang name|lang|{lang}}} translation}}
Pages missing in {{lang info|{lang}}}: '''<onlyinclude>{count}</onlyinclude>''' in total. Data as of {date}.

'''Notice:''' Please do not translate any of the articles in the [[WebAPI]] namespace, as the language is very technical and can lead to loss of context and meaning.

; See also
* [[TFW:Reports/All articles/{lang}|All articles in {{lang name|name|{lang}}}]]
* [[TFW:Reports/Missing translations/{lang}|Missing article translations in {{lang name|name|{lang}}}]]
* [[Special:RecentChangesLinked/Project:Reports/All articles/{lang}|Recent changes to articles in {{lang name|name|{lang}}}]]

== List ==
""".format(
			lang=language,
			count=len(translations[language]),
			date=strftime(r'%H:%M, %d %B %Y', gmtime()))
		output += '#%s\n'.join(sorted(translations[language]))
		outputs.append([language, output.encode('utf-8')])
	return outputs

if __name__ == '__main__':
	verbose = True
	f = open('wiki_undocumented_templates.txt', 'wb')
	for lang, output in main():
		f.write('\n===== %s =====\n' % lang)
		f.write(output)
	print 'Article written to wiki_undocumented_templates.txt'
	f.close()
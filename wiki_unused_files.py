from re import finditer, search
from urllib import unquote
from urllib2 import urlopen
from time import strftime, gmtime
languages = 'en, ar, cs, es, da, de, fi, fr, hu, it, ja, ko, nl, no, pl, pt, pt-br, ro, ru, sv, tr, zh-hans, zh-hant'.split(', ')
full_languages = 'English, Arabic, Czech, Spanish, Danish, German, Finnish, French, Hungarian, Italian, Japanese, Korean, Dutch, Norwegian, Polish, Portuguese, Portuguese (Brazil), Romanian, Russian, Swedish, Turkish, Chinese (Simplified), Chinese (Traditinal)'.split(', ')
exts = 'png, jpg, jpeg, mp3, wav, txt, gif'.split(', ')

def main():
	step = 500
	unused_files = []
	i = 0
	while (True):
		data = urlopen("https://wiki.teamfortress.com/wiki/Special:UnusedFiles?limit=%d&offset=%d" % (step, i)).read()
		m = search('There are no results for this report\.', data)
		if m is not None:
			break
		for m in finditer('data-url="(.*?)"', data):
			file = search('(.*)/(1024px-|)(.*)\.(.*)', m.group(1))
			lang = file.group(3).split('_')[-1]
			if lang in languages:
				lang = languages.index(lang)
			else:
				lang = 0
			unused_files.append([file.group(3), unquote(file.group(4)).lower(), lang])
		i += step
		print i
	unused_files.sort(key=lambda s: (exts.index(s[1]), s[2], s[0]))
	output = '{{DISPLAYTITLE:%d unused files}}\nUnused files, parsed from [[Special:UnusedFiles]]. Data accurate as of %s.' % (len(unused_files), strftime(r'%H:%M, %d %B %Y', gmtime()))
	type = ''
	lang = -1
	for file in unused_files:
		if file[0][:5] == 'User_':
			unused_files.remove(file)
			continue
		if file[0][:9] == 'Backpack_':
			unused_files.remove(file)
			continue
		if file[0][:4] == 'BLU_':
			unused_files.remove(file)
			continue
		if file[0][:10] == 'Item_icon_':
			unused_files.remove(file)
			continue
		if type != file[1].upper():
			type = file[1].upper()
			output += '== %s ==\n' % type
			lang = -1
		if lang != file[2]:
			lang = file[2]
			output += '=== %s ===\n' % full_languages[lang]
		output += '*[[Special:WhatLinksHere/File:%s|%s]]\n' % (file[0]+'.'+file[1], unquote(file[0])+'.'+file[1])
	return output

if __name__ == '__main__':
	f = open('wiki_unused_files.txt', 'wb')
	f.write(main())
	print("Article written to wiki_unused_files.txt")
	f.close()

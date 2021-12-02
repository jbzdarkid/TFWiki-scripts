from re import sub
from wikitools import wiki
from wikitools.page import Page
from time import gmtime, strftime

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

def main():
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  all_pages = {language: set() for language in LANGS}
  for page in w.get_all_pages():
    lang_suffix = page['title'].rpartition('/')[2]
    if lang_suffix in LANGS:
      all_pages[lang_suffix].add(page['title'])
    else:
      # There are apparently some exceptions here, according to seb__
      # badguys = [ 'OTFWH', 'titles', 'Archive', 'Header', 'Footer', 'diff' ]
      all_pages['en'].add(page['title'])

  outputs = []
  for language in LANGS:
    output = """
{{{{DISPLAYTITLE: {count} pages in {{{{lang name|name|{lang}}}}}}}}}
All articles in {{{{lang info|{lang}}}}}; '''<onlyinclude>{count}</onlyinclude>''' in total. Data as of {date}.

; See also
* [[Project:Reports/Missing translations/{lang}|Missing translations in {{{{lang name|name|{lang}}}}}]]
* [[Special:RecentChangesLinked/Project:Reports/All articles/{lang}|Recent changes to articles in {{{{lang name|name|{lang}}}}}]]

== List ==""".format(
      lang=language,
      count=len(all_pages[language]),
      date=strftime(r'%H:%M, %d %B %Y', gmtime()))
    if language == 'en': # Fixup, because english doesn't have translations
      output = output.replace('{{lang name|name|en}}', 'English')
      output = sub('\n.*?Missing translations/en.*?\n', '\n', output)

    for page in sorted(all_pages[language]):
      output += f'\n# [[{page}]]'
    outputs.append([language, output])
  return outputs

if __name__ == '__main__':
  verbose = True
  f = open('wiki_all_articles.txt', 'w')
  for lang, output in main():
    f.write(f'\n===== {lang} =====\n')
    f.write(output)
  print('Article written to wiki_all_articles.txt')
  f.close()

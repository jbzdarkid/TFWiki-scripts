from re import sub
from time import gmtime, strftime
from wikitools import wiki

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

def main(w):
  all_pages = {language: set() for language in LANGS}
  all_english_pages = set()
  for page in w.get_all_pages():
    basename, _, lang = page['title'].rpartition('/')
    if lang in LANGS:
      all_pages[lang].add(basename)
    elif 'OTFWH' in page['title']: # ETF2L Highlander Community Challenge/OTFWH
      pass # Do not translate
    else:
      all_english_pages.add(page['title'])

  outputs = []
  for language in LANGS:
    output = """\
{{{{DISPLAYTITLE: {count} pages in {{{{lang name|name|{lang}}}}}}}}}
All articles in {{{{lang info|{lang}}}}}; '''<onlyinclude>{count}</onlyinclude>''' in total. Data as of {date}.

; See also
* [[Project:Reports/Missing translations/{lang}|Missing translations in {{{{lang name|name|{lang}}}}}]]
* [[Project:Reports/Missing categories/{lang}|Missing categories in {{{{lang name|name|{lang}}}}}]]
* [[Special:RecentChangesLinked/Project:Reports/All articles/{lang}|Recent changes to articles in {{{{lang name|name|{lang}}}}}]]

== List ==""".format(
      lang=language,
      count=len(all_pages[language]),
      date=strftime(r'%H:%M, %d %B %Y', gmtime()))

    if language == 'en': # Fixup, because english doesn't have translations
      output = output.replace('{{lang name|name|en}}', 'English')
      output = sub('\n.*?Missing translations/en.*?\n', '\n', output)

    for page in sorted(all_pages[language]):
      output += f'\n# [[{page}/{language}]]'
    outputs.append([language, output])

  english_output = """\
{{{{DISPLAYTITLE: {count} pages in {{{{lang name|name|en}}}}}}}}
List of all English articles; <onlyinclude>{count}</onlyinclude> in total. Data as of {date}.

* ''See also:'' [[Special:RecentChangesLinked/Team Fortress Wiki:Reports/All articles/en|Recent changes to English articles]]

== List ==""".format(
    count=len(all_english_pages),
    date=strftime(r'%H:%M, %d %B %Y', gmtime()))
  for page in sorted(all_english_pages):
    english_output += f'\n# [[{page}]]'

  outputs.append(['en', english_output])

  return outputs

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_all_articles.txt', 'w') as f:
    for lang, output in main(w):
      f.write(f'\n===== {lang} =====\n')
      f.write(output)
  print(f'Article written to {f.name}')

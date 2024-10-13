from re import sub
from utils import time_and_date
from wikitools import wiki

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

def main(w):
  all_pages = {language: set() for language in LANGS}
  all_english_pages = set()
  for page in w.get_all_pages(namespaces=['Main', 'Help']):
    if 'OTFWH' in page.title: # ETF2L Highlander Community Challenge/OTFWH
      pass # Do not translate
    elif page.lang == 'en':
      all_english_pages.add(page)
    else:
      all_pages[page.lang].add(page)

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
      date=time_and_date())

    if language == 'en': # Fixup, because english doesn't have translations
      output = output.replace('{{lang name|name|en}}', 'English')
      output = sub('\n.*?Missing translations/en.*?\n', '\n', output)

    for page in sorted(all_pages[language]):
      output += f'\n# [[:{page.title}]]'
    outputs.append([language, output])

  english_output = """\
{{{{DISPLAYTITLE: {count} pages in {{{{lang name|name|en}}}}}}}}
List of all English articles; <onlyinclude>{count}</onlyinclude> in total. Data as of {date}.

* ''See also:'' [[Special:RecentChangesLinked/Team Fortress Wiki:Reports/All articles/en|Recent changes to English articles]]

== List ==""".format(
    count=len(all_english_pages),
    date=time_and_date())
  for page in sorted(all_english_pages):
    english_output += f'\n# [[:{page.title}]]'

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

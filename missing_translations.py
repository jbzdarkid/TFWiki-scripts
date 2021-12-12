from time import gmtime, strftime
from wikitools import wiki

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

def main(w):
  all_pages = set()
  english_pages = set()
  for page in w.get_all_pages():
    all_pages.add(page['title'])
    if page['title'].rpartition('/')[2] in LANGS:
      pass # Not english
    elif 'OTFWH' in page['title']: # ETF2L Highlander Community Challenge/OTFWH
      pass # Do not translate
    else:
      english_pages.add(page['title'])

  outputs = []
  for language in LANGS:
    missing_pages = set()
    for page in english_pages:
      if f'{page}/{language}' not in all_pages:
        missing_pages.add(page)

    output = """\
{{{{DISPLAYTITLE: {count} pages missing {{{{lang name|name|{lang}}}}} translation}}}}
Pages missing in {{{{lang info|{lang}}}}}: '''<onlyinclude>{count}</onlyinclude>''' in total. Data as of {date}.

; See also
* [[Project:Reports/All articles/{lang}|All articles in {{{{lang name|name|{lang}}}}}]]
* [[Special:RecentChangesLinked/Project:Reports/All articles/{lang}|Recent changes to articles in {{{{lang name|name|{lang}}}}}]]

== List ==""".format(
      lang=language,
      count=len(missing_pages),
      date=strftime(r'%H:%M, %d %B %Y', gmtime()))
    for page in sorted(missing_pages):
      output += f'\n#[[{page}]] ([[{page}/{language}|create]])'
    outputs.append([language, output])
  return outputs

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_missing_translations.txt', 'w') as f:
    for lang, output in main():
      f.write('\n===== %s =====\n' % lang)
      f.write(output)
  print('Article written to {f.name}')

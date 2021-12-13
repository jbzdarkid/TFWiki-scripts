from time import gmtime, strftime
from wikitools import wiki

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

def main(w):
  all_cats = set()
  english_cats = set()
  for page in w.get_all_categories():
    all_cats.add(page.title)
    if page.title.rpartition('/')[2] in LANGS:
      pass # Not english
    else:
      english_cats.add(page.title)

  outputs = []
  for language in LANGS:
    missing_cats = set()
    for page in english_cats:
      if f'{page}/{language}' not in all_cats:
        missing_cats.add(page)

    output = """\
{{{{DISPLAYTITLE: {count} categories missing {{{{lang name|name|{lang}}}}} translation}}}}
Categories missing in {{{{lang info|{lang}}}}}: '''<onlyinclude>{count}</onlyinclude>''' in total. Data as of {date}.

; See also
* [[Project:Reports/All articles/{lang}|All articles in {{{{lang name|name|{lang}}}}}]]
* [[Project:Reports/Missing translations/{lang}|Missing translations in {{{{lang name|name|{lang}}}}}]]
* [[Special:RecentChangesLinked/Project:Reports/All articles/{lang}|Recent changes to articles in {{{{lang name|name|{lang}}}}}]]

== List ==""".format(
      lang=language,
      count=len(missing_cats),
      date=strftime(r'%H:%M, %d %B %Y', gmtime()))
    for page in sorted(missing_cats):
      output += f'\n* [[:{page}]] ([[:{page}/{language}|create]])'
    outputs.append([language, output])
  return outputs

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_missing_translations.txt', 'w') as f:
    for lang, output in main(w):
      f.write('\n===== %s =====\n' % lang)
      f.write(output)
  print(f'Article written to {f.name}')

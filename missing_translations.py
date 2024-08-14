from utils import plural, time_and_date
from wikitools import wiki

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']
sort_by_count = True


def main(w):
  all_pages = {lang:set() for lang in LANGS}
  english_pages = set()
  for page in w.get_all_pages():
    if page.lang != 'en':
      all_pages[page.lang].add(page.basename)
    elif 'OTFWH' in page.title: # ETF2L Highlander Community Challenge/OTFWH
      pass # Special, non-translated page
    elif page.title.startswith('WebAPI'):
      pass # WebAPI pages are very technical and shouldn't be translated.
    else:
      english_pages.add(page)

  if verbose:
    print(f'Done processing pages, found {len(english_pages)} english pages')

  # We are going to generate several outputs, one for each language. The rest of the code is language-specific.
  outputs = []
  for language in LANGS:
    missing_pages = []
    for page in english_pages:
      if page.basename not in all_pages[language]:
        missing_pages.append(page)

    if verbose:
      print(f'Found {len(missing_pages)} missing pages in {language}')

    output = """\
{{{{DISPLAYTITLE: {count} pages missing {{{{lang name|name|{lang}}}}} translation}}}}
Pages missing in {{{{lang info|{lang}}}}}: '''<onlyinclude>{count}</onlyinclude>''' in total. Data as of {date}.

; See also
* [[Team Fortress Wiki:Reports/All articles/{lang}|All articles in {{{{lang name|name|{lang}}}}}]]
* [[Special:RecentChangesLinked/Team Fortress Wiki:Reports/All articles/{lang}|Recent changes to articles in {{{{lang name|name|{lang}}}}}]]

== List ==""".format(
      lang=language,
      count=len(missing_pages),
      date=time_and_date())

    sort_key = {}
    if sort_by_count:
      sort_key = {page: sum(1 for _ in page.get_links()) for page in missing_pages}
      missing_pages.sort(key = lambda page: -sort_key[page])
    else:
      missing_pages.sort() # Alphabetical sort

    for page in missing_pages:
      output += f'\n# [[:{page.basename}]] ([[:{page.title}/{language}|create]])'
      if len(sort_key) > 0: # If we have link counts
        output += f' ({plural.links(sort_key[page])})'
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

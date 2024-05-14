from utils import plural, time_and_date
from wikitools import wiki

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

def main(w):
  all_pages = {lang:{} for lang in LANGS}
  english_pages = []
  for page in w.get_all_pages():
    all_pages.add(page.title)
    if page.lang != 'en':
      pass # Not english
    elif 'OTFWH' in page.title: # ETF2L Highlander Community Challenge/OTFWH
      pass # Special, non-translated page
    elif page.title.startswith('WebAPI'):
      pass # WebAPI pages are very technical and shouldn't be translated.
    else:
      english_pages.append(page)

  # We are going to generate several outputs, one for each language. The rest of the code is language-specific.
  outputs = []
  for language in LANGS:
    missing_pages = set()
    for page in english_pages:
      if page.basename not in all_pages[language]
        missing_pages.add(page)

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
    for page in sorted(missing_pages):
      link_count = page.get_links()
      output += f'\n# [[:{page.basename}]] ([[:{page.title}|create]]) ({plural.links(link_count)})'
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

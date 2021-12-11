from time import gmtime, strftime
from wikitools import wiki

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

def main():
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  all_pages = {language: set() for language in LANGS}
  for page in w.get_all_pages():
    basename, _, lang = page['title'].rpartition('/')
    if lang in LANGS:
      all_pages[lang].add(basename)
    else:
      all_pages['en'].add(page['title'])

  overtranslated = {language: set() for language in LANGS}
  count = 0

  for language in LANGS:
    if language == 'en':
      continue

    for page in sorted(all_pages[language]):
      if page not in all_pages['en']:
        if verbose:
          print(f'Page {page}/{language} has no english equivalent')
        overtranslated[language].add(page)
        count += 1

  output = """\
{{{{DISPLAYTITLE: {count} pages with no english equivalent}}}}
Translated articles which do not have a corresponding article in english (ignoring redirects). Data as of {date}.

""".format(
      count=count,
      date=strftime(r'%H:%M, %d %B %Y', gmtime()))

  for language in LANGS:
    if len(overtranslated[language]) == 0:
      continue

    output += '== {{lang name|name|%s}} ==\n' % language
    for page in sorted(overtranslated[language]):
      output += '* [[%s/%s]] does not have a non-redirect english equivalent: [[%s]]\n' % (page, language, page)

  return output


if __name__ == '__main__':
  verbose = True
  f = open('wiki_overtranslated.txt', 'w')
  f.write(main())
  print('Article written to wiki_overtranslated.txt')
  f.close()

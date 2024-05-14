from utils import time_and_date
from wikitools import wiki
from wikitools.page import Page

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

def main(w):
  non_article_categories = set()
  for page in Page(w, 'Template:Non-article category').get_transclusions(namespace='Category'):
    non_article_categories.add(page.title)
  if verbose:
    print(f'Found {len(non_article_categories)} non-article categories')

  signal = object()

  lang_cats = {lang: set() for lang in LANGS}
  english_cats = set()
  for page in w.get_all_categories():
    if page.title in non_article_categories:
      continue # Tracking/maintenance/user categories

    if page.lang != 'en':
      lang_cats[page.lang].add(page.basename)
    else:
      is_empty = next(w.get_all_category_pages(page.title), signal) == signal
      if is_empty:
        if verbose:
          print(f'English category {page.title} is empty, skipping')
      else:
        english_cats.add(page.title)

  if verbose:
    print(f'Found {len(english_cats)} english article categories')

  english_only_cats = english_cats.copy()
  for lang_cat in lang_cats.values():
    english_only_cats -= lang_cat

  if verbose:
    print(f'Found {len(english_only_cats)} english-only categories')

  outputs = []
  output = """\
{{{{DISPLAYTITLE: {count} categories which are probably non-article categories}}}}
There are <onlyinclude>{count}</onlyinclude> categories which are not translated into any language other than english. These categories should probably transclude {{{{tl|Non-article category}}}}. Data as of {date}.

== List ==""".format(
    count=len(english_only_cats),
    date=time_and_date())

  for page in sorted(english_only_cats):
    output += f'\n# [[:{page}]]'
  outputs.append(['en', output])

  for language in LANGS:
    missing_cats = english_cats - lang_cats[language] - english_only_cats
    if verbose:
      print(f'{language} is missing {len(missing_cats)} categories')

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
      date=time_and_date())
    for page in sorted(missing_cats):
      output += f'\n# [[:{page}]] ([[:{page}/{language}|create]])'
    outputs.append([language, output])
  return outputs

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_missing_categories.txt', 'w') as f:
    for lang, output in main(w):
      f.write('\n===== %s =====\n' % lang)
      f.write(output)
  print(f'Article written to {f.name}')

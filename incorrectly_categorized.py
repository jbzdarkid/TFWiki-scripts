from utils import pagescraper_queue, time_and_date
from wikitools import wiki
from wikitools.page import Page

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

def pagescraper(category, w, miscategorized):
  cat_lang = category.rpartition('/')[2]
  if cat_lang not in LANGS:
    cat_lang = 'en'
  for page in w.get_all_category_pages(category):
    page_lang = page.title.rpartition('/')[2]
    if page_lang not in LANGS:
      page_lang = 'en'
    if page_lang != cat_lang:
      if category not in miscategorized[cat_lang]:
        miscategorized[cat_lang][category] = [page]
      else:
        miscategorized[cat_lang][category].append(page)

def main(w):
  # TODO: Consider including /lang categories again
  # TODO: Mark these as non-article
  maintanence_categories = [
    'Category:Community strategy stubs/lang',
    'Category:Custom maps unreleased stubs/lang',
    'Category:GFDL images',
    'Category:Images that need improving',
    'Category:Lists to be expanded',
    'Category:Protected pages',
    'Category:Quotations needing translating',
    'Category:Translating into Arabic',
    'Category:Translating into Chinese (Simplified)',
    'Category:Translating into Chinese (Traditional)',
    'Category:Translating into Czech',
    'Category:Translating into Danish',
    'Category:Translating into Dutch',
    'Category:Translating into Finnish',
    'Category:Translating into French',
    'Category:Translating into German',
    'Category:Translating into Hungarian',
    'Category:Translating into Italian',
    'Category:Translating into Japanese',
    'Category:Translating into Korean',
    'Category:Translating into Norwegian',
    'Category:Translating into Polish',
    'Category:Translating into Portuguese (Brazil)',
    'Category:Translating into Portuguese',
    'Category:Translating into Romanian',
    'Category:Translating into Russian',
    'Category:Translating into Spanish',
    'Category:Translating into Swedish',
    'Category:Translating into Turkish',
    'Category:Translations needing updating',
    'Category:Uses Full Moon templates/lang',
  ]

  for page in Page(w, 'Template:Non-article category').get_transclusions(namespace='Category'):
    maintanence_categories.append(page.title)

  miscategorized = {lang: {} for lang in LANGS}
  with pagescraper_queue(pagescraper, w, miscategorized) as categories:
    for category in w.get_all_categories(filter_redirects=False):
      if category.title not in maintanence_categories:
        if verbose:
          print(f'Processing {category}')
        categories.put(category.title)

  unique_pages = set()
  for language in LANGS:
    for pages in miscategorized[language].values():
      unique_pages.update(page.title for page in pages)

  output = """\
{{{{DISPLAYTITLE: {page_count} miscategorized pages}}}}
{category_count} categories have pages from other languages ('''<onlyinclude>{page_count}</onlyinclude>''' total pages). Data as of {date}.

{{{{TOC limit|2}}}}
""".format(
    category_count=len(miscategorized),
    page_count=len(unique_pages),
    date=time_and_date())

  for language in LANGS:
    if len(miscategorized[language]) == 0:
      continue

    category_keys = []
    for category in miscategorized[language]:
      category_keys.append([len(miscategorized[language][category]), category])
      if verbose:
        print(f'{category} has {category_keys[-1][0]} miscategorized pages')

    if verbose:
      print(f'{len(category_keys)} categories with bad pages in {language}')

    output += '== {{lang name|name|%s}} ==\n' % language
    for _, category in sorted(category_keys, reverse=True):
      output += f'=== [[:{category}]] ===\n'
      if verbose:
        print(f'  {len(miscategorized[language][category])} pages in category {category}')
      for page in sorted(miscategorized[language][category]):
        output += f'* [{page.get_edit_url()} {page.title}]\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_incorrectly_categorized.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

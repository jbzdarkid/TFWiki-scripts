from utils import pagescraper_queue, time_and_date
from wikitools import wiki
from wikitools.page import Page

verbose = False

def pagescraper(category, w, miscategorized):
  for page in w.get_all_category_pages(category.title):
    if page.lang != category.lang:
      if page.title not in miscategorized:
        miscategorized[page.title] = {
          'page': page,
          'categories': [],
        }
      miscategorized[page.title]['categories'].append(category.title)

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

  miscategorized = {}
  with pagescraper_queue(pagescraper, w, miscategorized) as categories:
    for category in w.get_all_categories(filter_redirects=False):
      if category.title not in maintanence_categories:
        if verbose:
          print(f'Processing {category.title}')
        categories.put(category)

  output = """\
{{{{DISPLAYTITLE: {page_count} miscategorized pages}}}}
<onlyinclude>{page_count}</onlyinclude> pages are in a category in another language. Data as of {date}.

{{{{TOC limit|2}}}}
""".format(
    page_count=len(miscategorized),
    date=time_and_date())

  for page_title in sorted(miscategorized.keys()):
    page = miscategorized[page_title]['page']
    output += f'=== [{page.get_edit_url()} {page.title}] ===\n'
    for category in sorted(miscategorized[page_title]['categories']):
      output += f'* [[:{category}]]\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_incorrectly_categorized.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

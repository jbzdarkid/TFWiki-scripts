from time import gmtime, strftime
from wikitools import wiki

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

def main(w):
  # TODO: Filter based on Category:Maintenance?
  # https://wiki.teamfortress.com/w/api.php?action=query&list=categorymembers&cmtitle=Category:Maintenance&cmnamespace=14
  maintanence_categories = [
    'Articles needing videos',
    'Articles marked for grammar correction/lang',
    'Articles marked for open review',
    'Articles needing 3D views',
    'Articles needing copy-editing',
    'Articles needing images',
    'Community strategy stubs/lang',
    'Custom maps unreleased stubs/lang',
    'ERROR',
    'Featured articles/lang',
    'Featured articles (Classic)/lang',
    'GFDL images',
    'Images that need improving',
    'Item infobox usage',
    "Item infobox using 'loadout-name'",
    "Item infobox using 'loadout-prefix'",
    'Language redirects',
    'Level ERROR',
    'Lists to be expanded',
    'Map infobox outdated parameters',
    'Maps without a screenshot',
    'Marked for deletion',
    'Needs Template Translation',
    'Out of date pages', # I wish I didn't have to do this but it's misreporting.
    'Out of date pages/lang',
    'Outdated Backpack item parameters',
    'Pages needing citations',
    'Pages requiring retranslation',
    'Pages using duplicate arguments in template calls',
    'Pages using invalid self-closed HTML tags',
    'Pages where node count is exceeded',
    'Pages where template include size is exceeded',
    'Pages with broken file links',
    'Pages with reference errors',
    'Pages with too many expensive parser function calls',
    'Protected pages',
    'Quotations needing translating',
    'Strange rank name ERROR',
    'Stubs/lang',
    'Translating into Arabic',
    'Translating into Chinese (Simplified)',
    'Translating into Chinese (Traditional)',
    'Translating into Czech',
    'Translating into Danish',
    'Translating into Dutch',
    'Translating into Finnish',
    'Translating into French',
    'Translating into German',
    'Translating into Hungarian',
    'Translating into Italian',
    'Translating into Japanese',
    'Translating into Korean',
    'Translating into Norwegian',
    'Translating into Polish',
    'Translating into Portuguese',
    'Translating into Portuguese (Brazil)',
    'Translating into Romanian',
    'Translating into Spanish',
    'Translating into Swedish',
    'Translating into Turkish',
    'Translations needing updating',
    'Templates that use translation switching',
    'Uses Full Moon templates/lang',
  ]

  miscategorized = {}
  category_keys = {language: [] for language in LANGS}
  unique_pages = set()
  for category in w.get_all_categories():
    category = category['*']
    if category in maintanence_categories:
      continue

    cat_lang = category.rpartition('/')[2]
    if cat_lang not in LANGS:
      cat_lang = 'en'
    for page in w.get_all_category_pages(category):
      page = page['title']
      page_lang = page.rpartition('/')[2]
      if page_lang not in LANGS:
        page_lang = 'en'
      if page_lang != cat_lang:
        if category not in miscategorized:
          miscategorized[category] = [page]
        else:
          miscategorized[category].append(page)
        unique_pages.add(page)
    if category in miscategorized: # We actually found pages
      category_keys[cat_lang].append([len(miscategorized[category]), category])
      if verbose:
        print(f'Category:{category} has {len(miscategorized[category])} miscategorized pages')

  output = """\
{{{{DISPLAYTITLE: {page_count} miscategorized pages}}}}
{category_count} categories have pages from other languages ('''<onlyinclude>{page_count}</onlyinclude>''' total pages). Data as of {date}.

{{{{TOC limit|2}}}}
""".format(
    category_count=len(miscategorized),
    page_count=len(unique_pages),
    date=strftime(r'%H:%M, %d %B %Y', gmtime()))

  for language in LANGS:
    if len(category_keys[language]) == 0:
      continue

    output += '== {{lang name|name|%s}} ==\n' % language
    for _, category in sorted(category_keys[language], reverse=True):
      output += f'=== [[:Category:{category}]] ===\n'
      for page in sorted(miscategorized[category]):
        output += '* [{{fullurl:%s|action=edit}} %s]\n' % (page, page)

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_incorrectly_categorized.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

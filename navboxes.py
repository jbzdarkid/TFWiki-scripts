from re import finditer, DOTALL
from time import gmtime, strftime
from wikitools import wiki
from wikitools.page import Page

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

# This wants something very specific so I'm not putting it into wikitools.
def get_navbox_templates(w):
  return w.get_with_continue('query', 'pages',
    generator='transcludedin',
    titles='Template:Navbox',
    gtinamespace=10, # Template:
    gtilimit=500,
  )

def main():
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')

  navbox_templates = {}
  for page in get_navbox_templates(w):
    p = Page(w, page['title']) 
    if p.title.lower().startswith('template:navbox'):
      continue # Exclude alternative navbox templates
    if p.title.lower().endswith('sandbox'):
      continue # Sandboxes link to pages but shouldn't be used
    if 'navbox' not in p.get_wiki_text().lower():
      continue # Some template pages actually *use* other navboxes, but are not one themselves.

    navbox_templates[p.title] = [
      set(link['title'] for link in p.get_links()),
      set(link['title'] for link in p.get_transclusions()),
    ]
    if verbose:
      print(f'Navbox {p.title} links to {len(navbox_templates[p.title][0])} pages and is transcluded by {len(navbox_templates[p.title][1])} pages')

  if verbose:
    print(f'Found {len(navbox_templates)} navbox templates')

  missing_navbox = {template: [] for template in navbox_templates}
  count = 0
  for page in w.get_all_pages():
    for template in navbox_templates:
      links, transclusions = navbox_templates[template]

      basename, _, lang = page['title'].rpartition('/')
      if lang not in LANGS:
        lang = 'en'
        basename = page['title']

      if basename in links and page['title'] not in transclusions:
        if verbose:
          print('Page', page['title'], 'is linked by', template, 'but does not transclude it')

        missing_navbox[template].append(page['title'])
        count += 1

  output = """\
{{{{DISPLAYTITLE:{count} pages missing navbox templates}}}}
Pages which a part of a navbox but do not include said navbox. Data as of {date}.

""".format(
      count=count,
      date=strftime(r'%H:%M, %d %B %Y', gmtime()))

  for template in missing_navbox:
    if len(missing_navbox[template]) == 0:
      continue

    output += f'== {template} ==\n'
    for page in sorted(missing_navbox[template]):
      output += f'* [[{page}]] does not transclude {template}\n'

    return output

if __name__ == '__main__':
  verbose = True
  f = open('wiki_navboxes.txt', 'w')
  f.write(main())
  print('Article written to wiki_navboxes.txt')
  f.close()

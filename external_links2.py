from re import compile, VERBOSE
from utils import pagescraper_queue, time_and_date
from wikitools import wiki

verbose = False

# Adapted from the old external_links_analyse.
LINK_REGEX = compile('''
  https?://         # Match http/https schemes
  [^\s[\]<>"]*?     # Match any number of interior characters: not whitespace nor []<>"
  [^\s[\]<>".:;,|)] # Match a single ending character: not whitespace nor []<>".:;,|)
''', VERBOSE)

NESTED_TEMPLATE_REGEX = compile('''
  {{            # Start of outer template
    ([^}]*?)    # Preceeding inner template
    {{(.*?)}}   # Inner template (note: may include further nesting)
    (.*?)       # Succeeding inner template
  }}            # End of outer template
''', VERBOSE)

TEMPLATE_PARAMS_REGEX = compile('''
  {{              # Start of template
    ([^}]*?[^ ])  # Characters preceeding a |, not already expanded
    |             # A | (argument separator)
    ([^ ][^}]*?)  # Characters succeeding a |, not already expanded
  }}
''', VERBOSE)
# Also shamelessly copied from the old external_links_analyse.
def get_links(regex, text):
  # First, clear out any nested templates and insert spaces around them
  new_text = None
  while new_text != text:
    new_text = NESTED_TEMPLATE_REGEX.sub(r'{{\1 \2 \3}}', text)
    text = new_text

  # Then, insert spaces around the | in the templates (to avoid including the control characters in the link
  while templateWithParamsR.search(text):
    text = templateWithParamsR.sub(r'{{ \1 | \2 }}', text)

  for m in regex.finditer(text):
    yield m.group('url')

# End of stuff I shamelessly copied.

def pagescraper(page):
  f

def link_verifier(link):

def main(w):
  page_links = {} # Map of page: [links]
  links = set()
  with pagescraper_queue(pagescraper) as pages:
    for page in w.get_all_pages():
      pages.put(page)








  output = """\
{{{{DISPLAYTITLE: {page_count} pages with broken external links}}}}
<onlyinclude>{page_count}</onlyinclude> pages have a broken or dangerous-looking external links. Data as of {date}.

{{{{TOC limit|2}}}}
""".format(
    page_count=0,
    date=time_and_date())

  link = link.replace('/', '&#47;')

  output += '= Dangerous links =\n'
  for page in sorted(dangerous_links.keys()):
    output += f'== [{page.get_edit_url()} {page.title}] ==\n'
    for link in dangerous_links[page]:
      output += f'* {link}\n'

  output += '= Broken links =\n'
  for domain in sorted(bad_links.keys()):
    output += f'== {domain} ==\n'
    domain_links = bad_links[domain])
    for page in sorted(domain_links.keys()):
      output += f'=== [{page.get_edit_url()} {page.title}] ===\n'
      for link in domain_links[page]:
        output += f'* {link}\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_external_links.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

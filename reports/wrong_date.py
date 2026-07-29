from collections import defaultdict
from re import search

from .utils import pagescraper_queue, time_and_date
from wikitools import wiki
from wikitools.page import Page

verbose = False
LANGS = ['en', 'ar', 'cs', 'da', 'de', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

def pagescraper(page, patches_per_page):
  text = page.get_wiki_text()
  
  patches = []
  depth = 0
  history_start = False
  for line in text.split('\n'):
    # There are some weird pages out there
    if search(r'{{[Uu]pdate[ _]history +\|', line):
      history_start = True
    if not history_start:
      continue

    # TODO: Special handling for sub-patches?
    m = search(r'{{[Pp]atch name\|(\d+)\|(\d+)\|(\d+)(.*?)}}', line)
    if m:
      # Normalize to a single key for simplicity
      patches.append(f'{m.group(3)}-{int(m.group(1)):02}-{int(m.group(2)):02}')

    # Assuming mismatched is doing its job, there should be an even count of {} within the page.
    # That means we can exit the loop once depth reaches 0 (and we exit the Update history section).
    depth += line.count('{') - line.count('}')
    if depth == 0:
      break

  if len(patches) > 0:
    patches_per_page[page.lang][page] = patches


def main(w):
  patches_per_page = {lang: {} for lang in LANGS}
  with pagescraper_queue(pagescraper, patches_per_page) as pages:
    # For now, only parse through pages which use {{Update history}}.
    # In the future, we could handle all pages which use {{Patch name}}.
    for page in Page(w, 'Template:Update history').get_transclusions(namespaces=['Main']):
      pages.put(page)

  # First, get the correct ordering
  expected_patches = {}
  for page, patches in patches_per_page['en'].items():
    expected_patches[page.title] = set(patches)

  # Next, check for errors.
  bad_order = {lang: [] for lang in LANGS}
  for lang in LANGS:
    for page, patches in patches_per_page[lang].items():
      # I only want to report two cases:
      # 1. The patch order is wrong (language independent)
      # 2. There's a patch which is backwards (month/date mixup)
      # I don't actually care about stale translations, nor even really about excessive translation, since both are just 'update your translation'.

      if patches != sorted(patches):
        bad_order[lang].append(page)
        if verbose:
          print(f'Page {page.title} has patches out of order')
        continue

      if page.basename in expected_patches:
        for patch in patches:
          if patch not in expected_patches[page.basename]:
            bad_order[lang].append(page)
            if verbose:
              print(f'Page {page.title} has a patch not in the english version')
            break

  output = """\
{{{{DISPLAYTITLE: {count} pages with incorrect patches}}}}
Found '''<onlyinclude>{count}</onlyinclude>''' pages where the patch links do not match english, or are not in chronological order. Data as of {date}.

{{{{TOC limit|2}}}}

""".format(
    count=sum((len(pages) for pages in bad_order.values())),
    date=time_and_date())

  for lang in LANGS:
    if len(bad_order[lang]) == 0:
      continue

    output += '== {{lang name|name|%s}} ==\n' % lang
    for page in sorted(bad_order[lang]):
      output += f'=== [[{page.title}]] ===\n'

      patches = patches_per_page[lang][page]
      for i in range(len(patches)):
        if i < len(patches) - 1 and patches[i+1] < patches[i]:
          output += f'Patch {patches[i]} is listed before {patches[i+1]}\n'
        if page.basename in expected_patches and patches[i] not in expected_patches[page.basename]:
          output += f'Patch {patches[i]} is not listed on the english page\n'

  return output

if __name__ == '__main__':
  import os
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php', user_agent=os.environ['USER_AGENT'])
  with open('wiki_wrong_date.txt', 'w', encoding='utf-8') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

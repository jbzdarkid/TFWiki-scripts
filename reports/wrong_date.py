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
    if search(r'{{[Uu]pdate[ _]history *\|', line):
      history_start = True
    if not history_start:
      continue

    m = search(r'{{[Pp]atch name\|(\d+)\|(\d+)\|(\d+)(.*?)}}', line)
    if m:
      print(m.group(0))
      patch_num = 0
      if m.group(4):
        for arg in m.group(4)[1:].split('|'):
          key, value = arg.split('=', 1)
          if key == 'num':
            patch_num = int(value)
            break

      # Normalize to (year, month, day) order for sorting
      patches.append((int(m.group(3)), int(m.group(1)), int(m.group(2)), patch_num))

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

  print(patches_per_page)

  # Determine the correct patch list, from the english page
  expected_patches = {}
  for page, patches in patches_per_page['en'].items():
    expected_patches[page.title] = set(patches)

  # Next, check for errors.
  bad_order = {lang: defaultdict(list) for lang in LANGS}
  flipped = {lang: defaultdict(list) for lang in LANGS}
  duplicates = {lang: defaultdict(list) for lang in LANGS}
  for lang in LANGS:
    for page, patches in patches_per_page[lang].items():
      # I only want to report these cases:
      # 1. The patch order is wrong (language independent)
      # 2. There's a patch which is backwards (month/date mixup)
      # 3. The same patch is listed twice (retranslation error)
      # I don't actually care about stale translations, nor even really about excessive translation, since both are just 'update your translation'.

      if patches != sorted(patches):
        for i, patch in enumerate(patches[:-1]):
          next_patch = patches[i+1]
          if patch > next_patch:
            bad_order[lang][page].append((f'{patch[0]}-{patch[1]:02}-{patch[2]:02}', f'{next_patch[0]:02}-{next_patch[1]:02}-{next_patch[2]:02}'))
        if verbose:
          print(f'Page {page.title} has patches out of order')
        continue

      if expected := expected_patches.get(page.basename, None):
        for patch in patches:
          flipped_patch = (patch[0], patch[2], patch[1])
          if patch not in expected and patch[1] != patch[2] and flipped_patch in expected and flipped_patch not in patches:
            flipped[lang][page].append((f'{patch[0]}-{patch[1]:02}-{patch[2]:02}', f'{patch[0]}-{patch[2]:02}-{patch[1]:02}'))
            if verbose:
              print(f'Page {page.title} has a (probable) day/month swapped patch')
            break

      unique_patches = set(patches)
      for patch in unique_patches:
        if patches.count(patch) > 1:
          duplicates[lang][page].append(f'{patch[0]}-{patch[1]:02}-{patch[2]:02}')
          if verbose:
            print(f'Page {page.title} lists {patch} twice')

  output = """\
{{{{DISPLAYTITLE: {count} pages with incorrect patches}}}}
Found '''<onlyinclude>{count}</onlyinclude>''' pages where the patch links do not match english, or are not in chronological order. Data as of {date}.

{{{{TOC limit|2}}}}

""".format(
    count=sum((len(pages) for pages in bad_order.values())),
    date=time_and_date())

  for lang in LANGS:
    pages = list(bad_order[lang].keys()) + list(flipped[lang].keys())
    if len(pages) == 0:
      continue

    output += '== {{lang name|name|%s}} ==\n' % lang
    for page in sorted(pages):
      output += '=== [[%s#{{heading|Update history|lang=%s}}|%s]] ===\n' % (page.title, page.lang, page.title)

      if page in bad_order[lang]:
        for error in bad_order[lang][page]:
          output += f'* Patch {error[0]} is listed before {error[1]}\n'
      if page in flipped[lang]:
        for error in flipped[lang][page]:
          output += f'* Page contains {error[0]}, but the english page only contains {error[1]}'
      if page in duplicates[lang]:
        for error in flipped[lang][page]:
          output += f'* Page lists {error} twice\n'

  return output

if __name__ == '__main__':
  import os
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php', user_agent=os.environ['USER_AGENT'])
  with open('wiki_wrong_date.txt', 'w', encoding='utf-8') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

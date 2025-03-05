from collections import defaultdict
from .utils import pagescraper_queue, time_and_date
from wikitools import wiki
from wikitools.page import Page

from .untranslated_templates import parse_lang_templates

verbose = False

REPEAT_USAGE_THRESHOLD = 5

def pagescraper(page, usage):
  lang_templates = parse_lang_templates(page)
  if verbose:
    print('Processing', page)

  for lang_template in lang_templates:
    english_text = None
    for lang, text in lang_template['args']:
      if lang == 'en':
        english_text = text
        break
    if not english_text:
      continue # Shouldn't happen; lang_quality checks for this. Avoids stupid errors, though.

    location = lang_template['location']
    usage[english_text].append((page, location))

def main(w):
  usage = defaultdict(list)
  with pagescraper_queue(pagescraper, usage) as pages:
    for page in w.get_all_templates():
      if page.title.startswith('Template:Dictionary'):
        continue # No reason to report on things already in the dictionary
      elif page.title.startswith('Template:PatchDiff'):
        continue # PatchDiff doesn't use the dictionary, save ourselves some time
      elif page.title == 'Template:Interface':
        continue # Manually excluded; this is a special mediawiki template
      elif page.title.startswith('Template:Mvm mission'):
        continue # These pages are agressively copy-pasted and poorly translated. I'm not dealing with them, here.
      pages.put(page)

  # Fetch strings which are already present in the dictionary.
  # The two main sources are common_strings and items.
  dictionary_strings = {}

  common_strings = Page(w, 'Template:Dictionary/common_strings')
  for line in common_strings.get_wiki_text().split('\n'):
    if line.startswith('  en: '):
      text = line.split(': ')[1].lower()
      dictionary_strings[text] = common_strings

  items = Page(w, 'Template:Dictionary/common_strings')
  for line in items.get_wiki_text().split('\n'):
    if line.startswith('  en: '):
      text = line.split(': ')[1].lower()
      dictionary_strings[text] = items

  print(list(dictionary_strings.keys())[:10])

  count = 0
  for key, value in usage.items():
    if key in dictionary_strings:
      count += 1
    elif len(value) >= REPEAT_USAGE_THRESHOLD:
      count += 1

  output = """\
{{{{DISPLAYTITLE: {count} lang strings which are in multiple places}}}}
Found '''<onlyinclude>{count}</onlyinclude>''' lang strings which should be moved to the dictionary, or are already there. Data as of {date}.

""".format(
    count=count,
    date=time_and_date())

  keys = list(usage.keys())
  keys.sort(key = lambda k: -len(usage[k]))
  for key in keys:
    value = usage[key]
    # Duplicates of dictionary entries
    if key in dictionary_strings:
      page = dictionary_strings[key]
      output += f'== <tt><nowiki>{key}</nowiki></tt> is already in [[{page.title}]] ==\n'
      for page, location in sorted(value):
        output += f'* [[{page.title}]] on {location}\n'

    # Used repeatedly (on the same page or different pages)
    elif len(value) >= REPEAT_USAGE_THRESHOLD:
      output += f'== <tt><nowiki>{key}</nowiki></tt> is used {len(value)} times ==\n'
      for page, location in sorted(value):
        output += f'* [[{page.title}]] on {location}\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_lang_duplicates.txt', 'w', encoding='utf-8') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

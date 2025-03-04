from collections import defaultdict
from .utils import pagescraper_queue, time_and_date
from wikitools import wiki

from untranslated_templates import parse_lang_templates

verbose = False

LANG_ORDER = 'en, ar, cs, da, de, es, fi, fr, hu, it, ja, ko, nl, no, pl, pt, pt-br, ro, ru, sv, tr, zh-hans, zh-hant'.split(', ')

def pagescraper(page, missing_english, invalid_langs, duplicate_langs, misordered_langs):
  lang_templates = parse_lang_templates(page)

  for lang_template in lang_templates:
    location = lang_template['location']

    # Error 1: Missing english string
    if not any((x[0] == 'en' for x in lang_template['args'])):
      missing_english[page].append(location)

    actual_order = []
    for lang, _ in lang_template['args']:
      if lang == '':
        continue # Usually the 'force' parameter, wrapped in an {{#if:}}, which gets simplified to nothing.
      try:
        idx = LANG_ORDER.index(lang)
      except ValueError:
        # Error 2: Invalid language codes
        invalid_langs[page][location].append(lang)
      else:
        actual_order.append(idx)

    # Error 3: Duplicate languages
    extra_langs = list(actual_order)
    for lang in set(actual_order):
      extra_langs.remove(lang)
    if len(extra_langs) > 0:
      duplicate_langs[page][location] = [LANG_ORDER[idx] for idx in extra_langs]

    # Error 4: Languages out of order
    expected_order = sorted(actual_order)
    for i, actual in enumerate(actual_order):
      if expected_order[i] != actual:
        misordered_langs[page][location] = (LANG_ORDER[expected_order[i]], LANG_ORDER[actual])
        break

def main(w):
  missing_english = defaultdict(list)
  invalid_langs = defaultdict(lambda: defaultdict(list))
  duplicate_langs = defaultdict(dict)
  misordered_langs = defaultdict(dict)
  with pagescraper_queue(pagescraper, missing_english, invalid_langs, duplicate_langs, misordered_langs) as pages:
    for page in w.get_all_templates():
      pages.put(page)

  output = """\
{{{{DISPLAYTITLE: {count} pages with lang errors}}}}
Found '''<onlyinclude>{count}</onlyinclude>''' pages with {{{{tl|lang}}}} errors. Data as of {date}.

""".format(
    count=len(missing_english) + len(invalid_langs) + len(duplicate_langs) + len(misordered_langs),
    date=time_and_date())

  if len(missing_english) > 0:
    output += '== Pages using {{tl|lang}} without an english string ==\n'
  for page in sorted(missing_english):
    output += f'=== [{page.get_edit_url()} {page.title}] ===\n'
    for location in missing_english[page]:
      output += f'* {location}\n'

  if len(invalid_langs) > 0:
    output += '== Pages using {{tl|lang}} without an invalid language code ==\n'
  for page in sorted(invalid_langs):
    output += f'=== [{page.get_edit_url()} {page.title}] ===\n'
    for location in invalid_langs[page]:
      langs = ', '.join(sorted(invalid_langs[page][location]))
      output += f'* {location}\n'
      output += f':Invalid lang codes: {langs}\n'

  if len(duplicate_langs) > 0:
    output += '== Pages using {{tl|lang}} with duplicate entries ==\n'
  for page in sorted(duplicate_langs):
    output += f'=== [{page.get_edit_url()} {page.title}] ===\n'
    for location in duplicate_langs[page]:
      langs = ', '.join(sorted(duplicate_langs[page][location]))
      output += f'* {location}\n'
      output += f':Duplicate lang codes: {langs}\n'

  if len(misordered_langs) > 0:
    output += '== Pages using {{tl|lang}} with out-of-order language codes ==\n'
  for page in sorted(misordered_langs):
    output += f'=== [{page.get_edit_url()} {page.title}] ===\n'
    for location in misordered_langs[page]:
      expected, actual = misordered_langs[page][location]
      output += f'* {location}\n'
      output += f':First out-of-order lang code: {actual}, expected {expected}\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_lang_quality.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

from collections import defaultdict
from utils import pagescraper_queue, time_and_date
from wikitools import wiki

from untranslated_templates import parse_lang_templates

verbose = False

LANG_ORDER = ['en', 'ar', 'cs', 'da', 'de', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

def pagescraper(page, errors):
  lang_templates = parse_lang_templates(page)

  for lang_template in lang_templates:
    location = lang_template.pop(0)

    missing_english = True
    for lang, _ in lang_template:
      if lang == 'en':
        missing_english = False

    # Error 0: Missing english string
    if missing_english:
      errors[0][page].append(location)

    actual_order = []
    for lang, _ in lang_template:
      idx = LANG_ORDER.find(lang)
      # Error 1: Invalid language codes (will probably show up as 'out of order' as well)
      if idx == -1:
        errors[1][page].append(location)
      else:
        actual_order.append(idx)

    # Error 2: Languages out of order
    if actual_order != sorted(actual_order):
      errors[2][page].append(location)

    # Error 3: Duplicate languages
    if len(actual_order) != len(set(actual_order)):
      errors[3][page].append(location)

def main(w):
  errors = [defaultdict(list) for _ in range(4)]
  with pagescraper_queue(pagescraper, errors) as pages:
    for page in w.get_all_templates():
      pages.put(page)

  output = """\
{{{{DISPLAYTITLE: {count} pages with lang errors}}}}
Found '''<onlyinclude>{count}</onlyinclude>''' pages with {{{{tl|lang}}}} errors. Data as of {date}.

""".format(
    count=sum((len(e) for e in errors)),
    date=time_and_date())

  if len(errors[0]) > 0:
    output += '== Pages using {{tl|lang}} without an english string ==\n'
  for page in errors[0]:
    output += f'=== [{page.get_edit_url()} {page.title}] ===\n'
    for location in errors[0][page]:
      output += f'* {location}\n'

  if len(errors[1]) > 0:
    output += '== Pages using {{tl|lang}} without an invalid language code ==\n'
  for page in errors[1]:
    output += f'=== [{page.get_edit_url()} {page.title}] ===\n'
    for location in errors[1][page]:
      output += f'* {location}\n'

  if len(errors[2]) > 0:
    output += '== Pages using {{tl|lang}} with out-of-order language codes ==\n'
  for page in errors[2]:
    output += f'=== [{page.get_edit_url()} {page.title}] ===\n'
    for location in errors[2][page]:
      output += f'* {location}\n'

  if len(errors[3]) > 0:
    output += '== Pages using {{tl|lang}} with duplicate entries ==\n'
  for page in errors[3]:
    output += f'=== [{page.get_edit_url()} {page.title}] ===\n'
    for location in errors[3][page]:
      output += f'* {location}\n'

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_lang_quality.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

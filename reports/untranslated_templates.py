from re import compile, IGNORECASE, VERBOSE
from .utils import pagescraper_queue, time_and_date, plural, whatlinkshere
from wikitools import wiki

counters = [0] * 100
from datetime import datetime

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

LANG_TEMPLATE_ARGS = compile(r"""
  \|        # Start of a parameter
  (
    [^|=]*? # Parameter
  )
  =         # Start of a value
  (
    [^|]*   # Value
  )
""", VERBOSE)

def parse_lang_templates(page):
  counters[0] -= datetime.now().timestamp()
  page_text = page.get_wiki_text()
  counters[0] += datetime.now().timestamp()

  counters[1] -= datetime.now().timestamp()
  buffer = {0: ''} # Text buffers for each level of the template, i.e. {{contains this text {{but not this text}} and still this text}}
  stack = [0] # Contains the indices which open the stack depth(s), i.e. the hierarchy of nested templates
  for i, char in enumerate(page_text):
    if char in '{[':
      stack.append(i)
      continue
    elif char in '}]':
      # The 'base' of the stack should not ever be popped (since it represents text at root scope)
      # If we get a mismatch just... do our best. Mismatched parens will be reported elsewhere.
      if len(stack) > 1:
        stack.pop() 
      continue

    # Add this character to the buffer for the current stack (or create the buffer if it doesn't exist)
    buffer[stack[-1]] = buffer.get(stack[-1], '') + char
  counters[1] += datetime.now().timestamp()

  if verbose:
    print(page.title, 'contains', len(buffer), 'pairs of braces')

  # Finally, search through for lang templates using regex
  lang_templates = []

  counters[2] -= datetime.now().timestamp()
  for index, text in buffer.items():
    template_name = text.split('|', 1)[0].strip()
    if not template_name.startswith('lang'):
      continue # We only care about {{lang}} and {{lang incomplete}}

    args = []
    first_arg_text = ''
    counters[3] -= datetime.now().timestamp()
    for match in LANG_TEMPLATE_ARGS.finditer(text):
      language = match.group(1).strip().lower()
      text = match.group(2).strip()
      args.append((language, text)) # Note that we're not using a dictionary here since some consumers care about duplicates
      if not first_arg_text:
        first_arg_text = text.split('\n', 1)[0].strip()
    counters[3] += datetime.now().timestamp()
    if not first_arg_text or first_arg_text == '':
      print(args)

    line_no = page_text[:index].count('\n') + 1
    lang_templates.append({
      'template': template_name,
      'args': args,
      'location': f"''Line {line_no}'': <nowiki>{first_arg_text}</nowiki>",
    })

  counters[2] += datetime.now().timestamp()
  return lang_templates

def pagescraper(page, translations, usage_counts):
  counters[4] -= datetime.now().timestamp()
  lang_templates = parse_lang_templates(page)
  counters[4] += datetime.now().timestamp()

  if len(lang_templates) == 0:
    return # Should be impossible (since we're looking for templates which transclude {{lang}}), but just in case.

  counters[5] -= datetime.now().timestamp()
  missing_translations = {lang:[] for lang in LANGS}
  for lang_template in lang_templates:
    if lang_template['template'] == 'lang incomplete':
      continue # Alternate lang template which indicates that we don't need full translation
    location = lang_template['location']

    missing_languages = set(LANGS)
    for lang, _ in lang_template['args']:
      missing_languages.discard(lang)

    for language in missing_languages:
      missing_translations[language].append(location)
  counters[5] += datetime.now().timestamp()

  if len(missing_translations) == 0:
    return # Template is fully translated, no need to report on it for anyone.

  counters[6] -= datetime.now().timestamp()
  usage_count = page.get_transclusion_count()
  counters[6] += datetime.now().timestamp()

  if usage_count == 0:
    return # Who cares, if it's not being used.

  usage_counts[page.title] = usage_count

  for lang, lang_missing_translations in missing_translations.items():
    if len(lang_missing_translations) > 0:
      translations[lang].append((page, lang_missing_translations))

def main(w):
  translations = {lang: [] for lang in LANGS}
  usage_counts = {}
  counters[7] -= datetime.now().timestamp()
  with pagescraper_queue(pagescraper, translations, usage_counts) as pages:
    # For performance, only search for templates which are reported to transclude lang/lang incomplete.
    pages_with_lang = set()
    pages_with_lang.union(Page(w, 'Template:Lang').get_transclusions(namespaces=['Template']))
    pages_with_lang.union(Page(w, 'Template:Lang incomplete').get_transclusions(namespaces=['Template']))
    for page in pages_with_lang:
      if '/' in page.title:
        continue # Don't include subpage templates like Template:Dictionary and Template:PatchDiff
      if page.title[:13] == 'Template:User':
        continue # Don't include userboxes
      if page.title == 'Template:Lang':
        continue # Special exclusion
      pages.put(page)
  counters[7] += datetime.now().timestamp()

  outputs = []
  for language in LANGS:
    output = """\
{{{{DISPLAYTITLE: {count} templates missing {{{{lang name|name|{lang}}}}} translation}}}}
Pages missing in {{{{lang info|{lang}}}}}: '''<onlyinclude>{count}</onlyinclude>''' in total. Data as of {date}.

; See also
* [[TFW:Reports/All articles/{lang}|All articles in {{{{lang name|name|{lang}}}}}]]
* [[TFW:Reports/Missing translations/{lang}|Missing article translations in {{{{lang name|name|{lang}}}}}]]
* [[Special:RecentChangesLinked/Project:Reports/All articles/{lang}|Recent changes to articles in {{{{lang name|name|{lang}}}}}]]

== List ==""".format(
      lang=language,
      count=len(translations[language]),
      date=time_and_date())

    counters[8] -= datetime.now().timestamp()
    for template, missing in sorted(translations[language], key=lambda elem: (-usage_counts[elem[0].title], elem[0].title)):
      count = usage_counts[template.title]
      output += f'\n# [{template.get_edit_url()} {template.title}] has [{whatlinkshere(template.title, count)} {plural.uses(count)}] and is missing {plural.translations(len(missing))}'
      for location in missing:
        output += f'\n#:{location}'
    counters[8] += datetime.now().timestamp()
    outputs.append([language, output])

  print('Counters', counters)
  return outputs

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_untranslated_templates.txt', 'w') as f:
    for lang, output in main(w):
      f.write('\n===== %s =====\n' % lang)
      f.write(output)
  print(f'Article written to {f.name}')

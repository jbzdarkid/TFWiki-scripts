from re import compile, IGNORECASE, VERBOSE
from .utils import pagescraper_queue, time_and_date, plural, whatlinkshere
from wikitools import wiki
from wikitools.page import Page

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

LANG_TEMPLATE_START = compile(r"""
  (?:^|[^{]){{      # The start of a template '{{' which is not the start of a parameter '{{{'
  \s*               # Any amount of whitespace is allowed before the template name
  lang              # Template name {{lang}}
  ([ ]incomplete)?  # Also matches {{lang incomplete}} but we can check which one it is by the first group
  \s*               # Any amount of whitespace (but critically, no more ascii characters)
  \|                # Start of parameter list
""", IGNORECASE | VERBOSE)

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


def parse_lang_templates2(page):
  page_text = page.get_wiki_text()

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

  # Finally, search through each template for a lang template, then parse the args via regex
  lang_templates = []

  for index, text in buffer.items():
    template_name = text.split('|', 1)[0].strip().lower()
    if template_name not in ['lang', 'lang incomplete']:
      continue
    if page_text[index-2:index+1] == '{{{':
      continue # Ignore 'lang' when it's used as an argument (as opposed to a template)

    args = []
    first_arg_text = None
    for match in LANG_TEMPLATE_ARGS.finditer(text):
      language = match.group(1).strip().lower()
      text = match.group(2).strip()
      args.append((language, text)) # Note that we're not using a dictionary here since some consumers care about duplicates
      if first_arg_text is None:
        first_arg_text = text.split('\n', 1)[0].strip()

    line_no = page_text[:index].count('\n') + 1
    lang_templates.append({
      'template': template_name,
      'args': args,
      'location': f"''Line {line_no}'': <nowiki>{first_arg_text if first_arg_text else ''}</nowiki>",
    })

  return lang_templates

def parse_lang_templates(page):
  page_text = page.get_wiki_text()

  # First, find the matching pairs
  def get_indices(char, string):
    index = -1
    indices = []
    while 1:
      try:
        index = string.index(char, index+1)
      except ValueError:
        break
      indices.append(index)
    return indices

  locations = [[len(page_text), -1]]
  for open in get_indices('{', page_text):
    locations.append([open, 1])
  for open in get_indices('[', page_text):
    locations.append([open, 1])
  for close in get_indices('}', page_text):
    locations.append([close, -1])
  for close in get_indices(']', page_text):
    locations.append([close, -1])
  locations.sort()

  # Next, divide the text up based on those pairs. Embedded text is separated out, e.g. {a{b}c} will become "ac" and "b".
  stack = [0]
  buffer = {0: ''}
  lastIndex = 0
  for index, value in locations:
    try:
      buffer[stack[-1]] = buffer.get(stack[-1], '') + page_text[lastIndex:index]
    except IndexError:
      buffer[0] += page_text[lastIndex:index] # Add text to default layer
      stack.append(None) # So there's something to .pop()
      if verbose:
        print(page.title, 'Found a closing brace without a matched opening brace')
    if value == 1:
      stack.append(index)
    elif value == -1:
      stack.pop()
    lastIndex = index + 1

  if verbose:
    print(page.title, 'contains', len(buffer), 'pairs of braces')

  # Finally, search through for lang templates using regex
  lang_templates = []

  for match in LANG_TEMPLATE_START.finditer(page_text):
    lang_template = {'args': []}
    # Skip the opening {{
    if match.group(0).startswith('{{'):
      search_text = buffer[match.start() + 1]
    else:
      search_text = buffer[match.start() + 2]
    for match2 in LANG_TEMPLATE_ARGS.finditer(search_text):
      language = match2.group(1).strip().lower()
      text = match2.group(2).strip()
      lang_template['args'].append((language, text))

    lang_template['location'] = "''Line %d'': <nowiki>%s</nowiki>" % (
      page_text[:match.start() + 1].count('\n') + 1,
      lang_template['args'][0][1].split('\n', 1)[0].strip() if len(lang_template['args']) > 0 else '',
    )

    lang_template['template'] = 'lang incomplete' if match.group(1) else 'lang'

    lang_templates.append(lang_template)

  return lang_templates

def pagescraper(page, translations, usage_counts):
  lang_templates = parse_lang_templates(page)
  lang_templates2 = parse_lang_templates2(page)
  if lang_templates != lang_templates2:
    print('v1/v2 mismatch for', page, len(lang_templates), len(lang_templates2))
    l1 = lang_templates
    l2 = lang_templates2
    assert len(l1) == len(l2), f'{len(l1)} != {len(l2)}\n{l1}\n{l2}'
    for i in range(len(l1)):
      assert l1[i]['template'] == l2[i]['template'], f'{l1[i]["template"]}\n!=\n{l2[i]["template"]}'
      assert l1[i]['location'] == l2[i]['location'], f'{l1[i]["location"]}\n!=\n{l2[i]["location"]}'
      assert l1[i]['args'] == l2[i]['args'], f'{l1[i]["args"]}\n!=\n{l2[i]["args"]}'

  if len(lang_templates) == 0:
    return # Should be impossible (since we're looking for templates which transclude {{lang}}), but just in case.

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

  if len(missing_translations) == 0:
    return # Template is fully translated, no need to report on it for anyone.

  usage_count = page.get_transclusion_count()

  if usage_count == 0:
    return # Who cares, if it's not being used.

  usage_counts[page.title] = usage_count

  for lang, lang_missing_translations in missing_translations.items():
    if len(lang_missing_translations) > 0:
      translations[lang].append((page, lang_missing_translations))

def main(w):
  translations = {lang: [] for lang in LANGS}
  usage_counts = {}
  with pagescraper_queue(pagescraper, translations, usage_counts) as pages:
    # For performance, only check template pages which are reported to transclude lang/lang incomplete.
    pages_with_lang = set()
    pages_with_lang.update(Page(w, 'Template:Lang').get_transclusions(namespaces=['Template']))
    pages_with_lang.update(Page(w, 'Template:Lang incomplete').get_transclusions(namespaces=['Template']))
    for page in pages_with_lang:
      if page.title[:13] == 'Template:User':
        continue # Don't include userboxes
      if page.title == 'Template:Lang':
        continue # Special exclusion
      pages.put(page)

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

    for template, missing in sorted(translations[language], key=lambda elem: (-usage_counts[elem[0].title], elem[0].title)):
      count = usage_counts[template.title]
      output += f'\n# [{template.get_edit_url()} {template.title}] has [{whatlinkshere(template.title, count)} {plural.uses(count)}] and is missing {plural.translations(len(missing))}'
      for location in missing:
        output += f'\n#:{location}'
    outputs.append([language, output])

  return outputs

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_untranslated_templates.txt', 'w') as f:
    for lang, output in main(w):
      f.write('\n===== %s =====\n' % lang)
      f.write(output)
  print(f'Article written to {f.name}')

from re import compile, IGNORECASE, VERBOSE
from utils import pagescraper_queue, time_and_date, plural, whatlinkshere
from wikitools import wiki

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

LANG_TEMPLATE_START = compile(r"""\
  [^{]{{    # The start of a template '{{' which is not the start of a parameter '{{{'
  \s*       # Any amount of whitespace is allowed before the template name
  lang      # Language template. Note that this does not allow invocations of {{lang incomplete}}
  \s*       # Any amount of whitespace (but critically, no more ascii characters)
  \|        # Start of parameter list
""", IGNORECASE | VERBOSE)

LANG_TEMPLATE_ARGS = compile(r"""\
  \|        # Start of a parameter
  (
    [^|=]*? # Parameter
  )
  =         # Start of a value
  (
    [^|]*   # Value
  )
""", VERBOSE)

def pagescraper(page, translations, usage_counts):
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
  for close in get_indices('}', page_text):
    locations.append([close, -1])
  locations.sort()

  # Next, divide the text up based on those pairs. Embedded text is separated out, e.g. {a{b}c} will become "ac" and "b".
  stack = [0]
  buffer = {0: ''}
  lastIndex = 0
  for index, value in locations:
    try:
      buffer[stack[-1]] += page_text[lastIndex:index]
    except KeyError: # New addition
      buffer[stack[-1]] = page_text[lastIndex:index]
    except IndexError: # Unmached parenthesis, e.g. Class Weapons Tables
      buffer[0] += page_text[lastIndex:index] # Add text to default layer
      stack.append(None) # So there's something to .pop()
      if verbose:
        print('Found a closing brace without a matched opening brace')
    if value == 1:
      stack.append(index)
    elif value == -1:
      stack.pop()
    lastIndex = index + 1

  if verbose:
    print(page.title, 'contains', len(buffer), 'pairs of braces')


  # Finally, search through for lang templates using regex
  missing_translations = {lang:[] for lang in LANGS}

  for match in LANG_TEMPLATE_START.finditer(page_text):
    line_no = str(page_text[:match.start()].count('\n') + 1)
    english_text = ''

    missing_languages = set(LANGS)
    for match2 in LANG_TEMPLATE_ARGS.finditer(buffer[match.start() + 2]): # Skip the opening {{
      language = match2.group(1).strip().lower()
      if language == 'en':
        english_text = match2.group(2).strip().split('\n', 1)[0].strip()
      missing_languages.discard(language)

    location = f"''Line {line_no}''"
    if english_text:
      location += f': <nowiki>{english_text}</nowiki>'
    for language in missing_languages:
      missing_translations[language].append(location)

    if verbose:
      line = page_text[:match.start()].count('\n') + 1
      print(f'Lang template at line {line} is missing translations for', ', '.join(sorted(missing_languages)))

  usage_count = page.get_transclusion_count()
  if usage_count == 0:
    return # Who cares, if it's not being used.

  usage_counts[page.title] =  usage_count

  for lang, lang_missing_translations in missing_translations.items():
    if len(lang_missing_translations) > 0:
      translations[lang].append((page, lang_missing_translations))

def main(w):
  translations = {lang: [] for lang in LANGS}
  usage_counts = {}
  with pagescraper_queue(pagescraper, translations, usage_counts) as pages:
    for page in w.get_all_templates():
      if '/' in page.title:
        continue # Don't include subpage templates like Template:Dictionary and Template:PatchDiff
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

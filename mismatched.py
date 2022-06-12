# coding: utf-8
from re import compile, IGNORECASE
from unicodedata import east_asian_width as width
from utils import pagescraper_queue, time_and_date
from wikitools import wiki

# Using the first group from https://www.unicode.org/Public/UNIDATA/extracted/DerivedBidiClass.txt
# which should include all of our arabic text on the wiki.
# Matches an arabic character, followed by any number of non-separators (newlines for articles or pipes for templates)
# A separator (| or \n) followed by any number of LTR characters, followed by an open paren

pairs = [
  [1, '\\(', '\\)'],
  [1, '（', '）'], # These parens are used interchangably with the ASCII ones.
  [2, '\\[', '\\]'],
  [3, '{', '}'],
  [4, '<!--', '-->'],
  [5, '<nowiki>', '</nowiki>'],
  [6, '<noinclude>', '</noinclude>'],
  [7, '<includeonly>', '</includeonly>'],
  [8, '<onlyinclude>', '</onlyinclude>'],
]
html_tags = [
  'a', 'b', 'code', 'center', 'em', 'i', 'li', 'ol', 'p', 's', 'small', 'sub', 'sup', 'td', 'th', 'tr', 'tt', 'u', 'ul',

  # Mediawiki custom
  'gallery', 'ref',
]
for tag in html_tags:
  # The tag open match needs to allow for properties, e.g. <div style="foo">
  pairs.append([f'<{tag}(?: [^>/]*)?>', f'</{tag}>'])

pairs = [[compile(pair[0], IGNORECASE), compile(pair[1], IGNORECASE)] for pair in pairs]

# Some pages are expected to have mismatched parenthesis (as they are part of the update history, item description, etc)
exemptions = {
  'Linux dedicated server': 0,   # Includes a bash script with case
  'List of default keys': 2,     # Includes {{Key|]}}
  'Deathcam': 2,                 # Includes {{Key|[}}
  'Scripting': 2,                # Includes {{key|]}} and {{key|[}}
}

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']


def pagescraper(page, translation_data):
  text = page.get_wiki_text()

  locations = []
  for i, left, right, in enumerate(pairs):
    if exemptions.get(page.basename, None) == i:
      continue

    for m in left.finditer(search_text):
      locations.append([m.start(), +(i+1)])

    for m in right.finditer(search_text):
      locations.append([m.start(), -(i+1)])

  locations.sort()

  errors = []
  opens = []

  in_nowiki = False
  in_comment = False
  for index, pair_index in locations:
    if pair_index == +5:
      in_nowiki = True
    elif pair_index == -5:
      in_nowiki = False
    elif pair_index == +4:
      in_comment = True
    elif pair_index == -4:
      in_comment = False
    elif in_nowiki or in_comment:
      continue # Ignore all escaped text (note that this may behave poorly for interleaved escapes)

    if pair_index > 0:
      opens.append([index, pair_index])
    elif pair_index < 0:
      if len(opens) == 0: # Closing tag without a matching opening
        if pair_index == -1: # Closing paren:
          if text[index-1] in [':', '1', '2', '3']:
            continue # Ignore extraneous parens caused by a smily face or numbered list
        errors.append(index)
      elif opens[-1][1] + pair_index == 0: # Matching
        opens.pop()
      elif len(opens) > 1 and opens[-2][1] + pair_index == 0: # This closing tag matches the n-1th opening tag (i.e. we have an extra opening tag)
        errors.append(opens.pop()[0]) # The mismatched opening tag
        opens.pop() # The matched opening tag
      elif len(opens) > 2 and opens[-3][1] + pair_index == 0: # This closing tag matches the n-2th opening tag (i.e. we have two extra opening tags)
        errors.append(opens.pop()[0]) # The first mismatched opening tag
        errors.append(opens.pop()[0]) # The second mismatched opening tag
        opens.pop() # The matched opening tag
      else: # Likely an extraneous closing tag
        errors.append(index)

  # Check for leftover opening tags that were not properly closed
  for index, pair_index in opens:
    if pair_index == +7 and page.title.startswith('Template:'):
      if verbose:
        print(f'Ignoring trailing noinclude on {page.title}')
      continue # Templates may leave off the closing </noinclude>, mediawiki figures it out.

    errors.append(index)

  if len(errors) > 0:
    if verbose:
      print(f'Found {len(errors)} errors for page {page.title}')
    data = f'<h3> [{page.get_edit_url()} {page.title}] </h3>\n'
    errors.sort()
    for error in errors:
      # For display purposes, we want to highlight the mismatched symbol. To do so, we replicate the symbol on the line below, at the same horizontal offset.
      # For sanity reasons, we don't want to show too long of a line.

      start = text.rfind('\n', error-60, error) # Find the start of the line (max 80 chars behind)
      if start == -1:
        start = max(0, error-60) # Not found
      else:
        start += 1 # We don't actually want to include the \n

      # Find the next EOL, potentially including >1 line if EOL is within 20 characters.
      end = text.find('\n', start+10, start+120)
      if end == -1:
        end = start+120

      # Compute additional padding for wide characters
      widths = [width(char) for char in text[start:error]]
      extra_width = int(widths.count('W') * 0.8) # Some padding because non-ascii characters are wide

      data += '<div class="mw-code"><nowiki>\n'
      data += text[start:end].replace('<', '&#60;') + '\n' # Escape <nowiki> and <onlyinclude> and other problem tags
      data += ' '*(error-start+extra_width) + text[error] + ' '*10 + '\n'
      data += '</nowiki></div>\n'

    translation_data[page.lang].append(data)

def main(w):
  translation_data = {lang: [] for lang in LANGS}
  with pagescraper_queue(pagescraper, translation_data) as pages:
    for page in w.get_all_pages(namespaces=['Main', 'File', 'Template', 'Help', 'Category']):
      if page.title.startswith('Team Fortress Wiki:Discussion'):
        continue
      if page.title.endswith(' 3D.jpg') or page.title.endswith(' 3D.png'):
        continue
      if page.title.startswith('File:User'):
        continue
      if page.title.startswith('Template:PatchDiff'):
        continue
      # Don't analyze the main dictionary pages, in case there's a mismatch which evens out between two strings
      if page.title.startswith('Template:Dictionary') and page.title.count('/') == 1: # Dictionary/items, e.g.
        continue
      if page.title.startswith('Template:Dictionary/achievements/') and page.title.count('/') == 2: # Dictionary/achievements/medic, e.g.
        continue
      if page.title.startswith('Template:Dictionary/steam ids'):
        continue # Usernames can be literally anything, but often include :)
      pages.put(page)
  output = """\
{{{{DISPLAYTITLE: {count} pages with mismatched parenthesis}}}}
<onlyinclude>{count}</onlyinclude> pages with mismatched <nowiki>(), [], and {{}}</nowiki>. Data as of {date}.
{{{{TOC limit|2}}}}

""".format(
    count=sum(len(lang_pages) for lang_pages in translation_data.values()),
    date=time_and_date())

  for language in LANGS:
    if len(translation_data[language]) > 0:
      output += '== {{lang name|name|%s}} ==\n' % language
      for data in translation_data[language]:
        output += data

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_mismatched_parenthesis.txt', 'w', encoding='utf-8') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

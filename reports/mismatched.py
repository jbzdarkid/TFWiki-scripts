# coding: utf-8
from re import compile, IGNORECASE
from unicodedata import east_asian_width as width
from .utils import pagescraper_queue, time_and_date
from wikitools import wiki

pairs = [
#  [1, '\\(', '\\)'],
#  [1, '（', '）'], # These parens are used interchangably with the ASCII ones.
  [2, '\\[', '\\]'],
  [3, '{', '}'],
  [4, '<!--', '-->'],
  [5, '<nowiki>', '</nowiki>'],
  [6, '<noinclude>', '</noinclude>'],
  [7, '<includeonly>', '</includeonly>'],
  [8, '<onlyinclude>', '</onlyinclude>'],
]
html_tags = [
  # This list does not include all html tags because we definitely cheat and don't close some of them, regularly.
  'a', 'b', 'code', 'center', 'em', 'li', 'ol', 'p', 's', 'small', 'sub', 'sup', 'td', 'th', 'tr', 'tt', 'u', 'ul',

  # Mediawiki custom
  'gallery', 'ref',
]
for tag in html_tags:
  # The tag open match needs to allow for properties, e.g. <div style="foo">
  pairs.append([pairs[-1][0] + 1, f'<{tag}(?: [^>/]*)?(?:"[^"]+")?>', f'</{tag}>'])

pairs = [[pair[0], compile(pair[1], IGNORECASE), compile(pair[2], IGNORECASE)] for pair in pairs]

# Some pages are expected to have mismatched parenthesis (as they are part of the update history, item description, etc)
exemptions = {
  # []
  2: ['List of default keys', 'Deathcam', 'Scripting', 'Vector', 'Linux dedicated server', 'Atoll'],

  # {} often don't align because template pages are using a header or footer for tables.
  3: [
    'Template:Cite web',
    'Template:Class speed table',
    'Template:Class weapons table',
    'Template:Contracts',
    'Template:Cqc',
    'Template:List of item attributes',
    'Template:Translation progress/stats/row',
    'Template:Userboxbottom',
    'Template:Userboxtop',
    'Template:Wqc',
  ],

  # <!-- --> is often messed up by The Heartsman, who has an >>--arrow---> through their name.
  4: ['Monster Mash-Up Pack', 'Night of the Living Update'],

  # <nowiki> and <noinclude> are often used to make template code *appear* correct, while still transcluding properly.
  5: ['Help:Images', 'Help:Editing', 'Help:Translation switching'],
  6: ['Help:Images'],

  # <includeonly> is used for subst-only templates, so that they do not show an error on the template page itself.
  7: ['Template:Sp'],

  # <code> is misaligned in this template to support a "plainlinks" style
  11: ['Template:Lang info'],

  # Complex wiki template which does custom <ul> stuff
  26: ['Template:Shortcut'],
}

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']


def pagescraper(page, translation_data):
  text = page.get_wiki_text()
  if page.title == 'List of official tips':
    lines = text.split('\n')
    buff_line = [line for line in lines if 'As a Soldier, activating the Buff Banner provides' in line]
    print('<74>', buff_line)

  locations = []
  for i, left, right, in pairs:
    if i in exemptions and any(page.basename.startswith(e) for e in exemptions[i]):
      continue

    for m in left.finditer(text):
      locations.append([m.start(), +i])

    for m in right.finditer(text):
      locations.append([m.start(), -i])

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
    if pair_index == +6 and page.title.startswith('Template:'):
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

    translation_data[page] = data

def page_iter(w):
  for page in w.get_all_pages(namespaces=['Main', 'File', 'Template', 'Help', 'Category']):
    yield page

def main(w):
  translation_data = {}
  with pagescraper_queue(pagescraper, translation_data) as pages:
    for page in page_iter(w):
      if page.title.startswith('Team Fortress Wiki:Discussion'):
        continue
      if page.title.endswith(' 3D.jpg') or page.title.endswith(' 3D.png'):
        continue
      if page.title.startswith('File:User'):
        continue
      if page.title.startswith('Template:PatchDiff'):
        continue
      if page.title == 'Template:Navbox':
        continue # Just too complex, mixes <td><tr> and templates, which results in hard-to-parse stuff.
      # Ignore sandbox pages, where things can and will be broken
      if page.title.lower().endswith('sandbox'):
        continue
      # Don't analyze the main dictionary pages, in case there's a mismatch which evens out between two strings
      if page.title.startswith('Template:Dictionary') and page.title.count('/') == 1: # Dictionary/items, e.g.
        continue
      if page.title.startswith('Template:Dictionary/achievements/') and page.title.count('/') == 2: # Dictionary/achievements/medic, e.g.
        continue
      if page.title.startswith('Template:Dictionary/steam ids'):
        continue # Usernames can be literally anything, and thus have no "matching" requirements
      pages.put(page)
  output = """\
{{{{DISPLAYTITLE: {count} pages with mismatched parenthesis}}}}
<onlyinclude>{count}</onlyinclude> pages with mismatched <nowiki>[], and {{}}</nowiki>. Data as of {date}.
{{{{TOC limit|2}}}}

""".format(
    count=len(translation_data),
    date=time_and_date())

  pages = sorted(list(translation_data.keys()))
  last_language = None
  for page in pages:
    if last_language != page.lang:
      last_language = page.lang
      output += '== {{lang name|name|%s}} ==\n' % page.lang
    output += translation_data[page]

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_mismatched_parenthesis.txt', 'w', encoding='utf-8') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

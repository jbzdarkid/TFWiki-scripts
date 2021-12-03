from json import loads
from queue import Queue, Empty
from threading import Thread, Event
from unicodedata import east_asian_width as width
from urllib.parse import quote
from wikitools import wiki
from wikitools.page import Page

pairs = [
  ['(', ')'],
  ['[', ']'],
  ['{', '}'],
  ['<', '>'],
  ['（', '）'],
]

verbose = False
PAGESCRAPERS = 50

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

def pagescraper(pages, done, page_data):
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  while True:
    try:
      page = Page(w, pages.get(True, 1)['title'])
    except Empty:
      if done.is_set():
        return
      else:
        continue

    text = page.get_wiki_text()
    errors = []
    for pair in pairs:
      locations = []
      for open in get_indices(pair[0], text):
        locations.append([open, 1])
      for close in get_indices(pair[1], text):
        locations.append([close, -1])
      locations.sort()

      opens = []
      for index, val in locations:
        if val == 1:
          opens.append(index)
        elif len(opens) == 0:
          errors.append(index) # Closing without opening
        else:
          opens.pop()

      errors.extend(opens) # Opening without closing

    if len(errors) > 0:
      if verbose:
        print(f'Found {len(errors)} errors for page {page.title}')
      data = f'=== [{page.get_edit_url()} {page.title}] ===\n'
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
        extra_width = widths.count('W') # + widths.count('F')

        data += '<pre>\n'
        data += text[start:end] + '\n'
        extra_width = int(widths.count('W') * 0.8) # ... a guess
        data += ' '*(error-start+extra_width) + text[error] + '\n'
        data += '</pre>\n'
      page_data[page.title] = data

def main():
  pages, done = Queue(), Event()
  page_data = {}
  threads = []
  for i in range(PAGESCRAPERS): # Number of threads
    thread = Thread(target=pagescraper, args=(pages, done, page_data))
    threads.append(thread)
    thread.start()
  try:
    w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
    for page in w.get_all_pages():
      pages.put(page)
      if page['title'].startswith('K'):
        break # There are a lot of pages in this report. Let's not go too crazy just yet.

  finally:
    done.set()
    for thread in threads:
      thread.join()
  
  LANGS = ['ar', 'cs', 'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']
  page_keys = sorted(page_data.keys())

  output = ''
  output += f'{{{{DISPLAYTITLE: {len(page_keys)} pages with mismatched parenthesis}}\n'
  output += '{{TOC limit|2}}\n'

  for language in LANGS:
    output += f'== {{{{lang info|{language}}}}} ==\n'
    for page in page_keys:
      if page.endswith(language):
        output += page_data[page]
      elif language == 'en':
        output += page_data[page]

  return output

if __name__ == '__main__':
  verbose = True
  f = open('wiki_mismatched_parenthesis.txt', 'w', encoding='utf-8')
  f.write(main())
  print('Article written to wiki_mismatched_parenthesis.txt')
  f.close()

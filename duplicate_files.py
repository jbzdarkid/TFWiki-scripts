from time import gmtime, strftime
from wikitools import wiki
from wikitools.page import Page

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

def main(w):
  seen = set()
  all_duplicates = []
  for page in w.get_all_files():
    duplicates = page.raw.get('duplicatefiles', [])
    duplicates = [ 'File:' + dupe['name'].replace('_', ' ') for dupe in duplicates ]

    # Normalize language titles, this means we treat 'Theshowdown05' and 'Theshowdown05 ru' as the same file.
    title = page.title.rpartition('.')[0]
    for lang in LANGS:
      if title.endswith(f' {lang}'):
        title = title[:-len(lang)-1]
        break

    if not duplicates or title in seen:
      continue
    duplicates += [title, page.title] # The duplicate list does not include ourselves, obviously

    if verbose:
      print(f'Found duplicate image: {page.title}')

    seen.update(duplicates)
    all_duplicates.append(duplicates)

  if verbose:
    print(f'Found {len(all_duplicates)} duplicate images')

  all_duplicates.sort(key = lambda dupe_list: -len(dupe_list)) # Put files with the most duplicates first

  output = """\
{{{{DISPLAYTITLE: {count} duplicate files}}}}
List of all duplicate files; <onlyinclude>{unique}</onlyinclude> unique files, {count} duplicated files in total. Data as of {date}.

== List ==\n""".format(
    unique = len(all_duplicates),
    count = sum(len(dupe_list) for dupe_list in all_duplicates),
    date = strftime(r'%H:%M, %d %B %Y', gmtime()))

  for dupe_list in all_duplicates:
    dupe_list = [d for d in dupe_list if not d.startswith('File:User')]
    if len(dupe_list) <= 1:
      continue

    counts = []
    for duplicate in dupe_list:
      link_count = Page(w, duplicate).get_file_link_count()
      counts.append([link_count, duplicate])

    counts.sort(key=lambda s: (-s[0], s[1]))

    output += f'[[{dupe_list[0]}|200px]]\n'
    for count, title in counts:
      output += '* [[:%s|]] ([{{fullurl:Special:WhatLinksHere/%s|limit=%d&namespace=0&hideredirs=1}} %d use%s])\n' % (title, title, min(50, count), count, '' if count == 1 else 's')
    output += '\n'
  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_duplicate_files.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

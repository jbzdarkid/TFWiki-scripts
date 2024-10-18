from wikitools import wiki

import missing_translations

# Flipping the 'sort_by_count' flag to, well, sort by count
missing_translations.sort_by_count = True

def main(w):
  return missing_translations.main(w)

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_missing_translations.txt', 'w') as f:
    for lang, output in main(w):
      f.write('\n===== %s =====\n' % lang)
      f.write(output)
  print(f'Article written to {f.name}')

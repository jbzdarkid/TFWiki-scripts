from time import strftime, gmtime
from wikitools import wiki
from wikitools.page import Page

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

def main(w):
  unused_files = {}
  count = 0
  for file in w.get_all_unused_files():
    if file.startswith('User'):
      continue # Users may upload files and not use them.
    if file.startswith('Backpack '):
      continue # These are provided in bulk to support {{Backpack item}}, but they may not specifically be used.
    # if file.startswith('Item icon '):
    #   continue
    if file.startswith('Tf') and file.endswith('.txt'):
      continue # Externally linked as part of Template:PatchDiff
    if file.endswith(' 3D.png'):
      p = Page(w, file)
      if p.get_transclusion_count() > 0:
        continue # The 3D viewer template transcludes files, instead of linking them.

    name, _, ext = file.rpartition('.')
    ext = ext.upper()
    if ext not in unused_files:
      unused_files[ext] = {language: set() for language in LANGS}
      if verbose:
        print('Found new file extension:', ext)

    for language in LANGS:
      if name.endswith(f' {language}'):
        unused_files[ext][language].add(file)
        count += 1
        break
    else:
      unused_files[ext]['en'].add(file)

  output = """\
{{{{DISPLAYTITLE:{count} unused files}}}}
<onlyinclude>{count}</onlyinclude> unused files, parsed from [[Special:UnusedFiles]]. Data as of {date}.

""".format(
  count=count,
  date=strftime(r'%H:%M, %d %B %Y', gmtime()))
  for ext in sorted(unused_files.keys()):
    output += f'== {ext} ==\n'
    for language in LANGS:
      language_files = unused_files[ext][language]
      if len(language_files) > 0:
        output += '=== {{lang name|name|%s}} ===\n' % language
        if language == 'en' and ext == 'PNG':
          output += 'Some of these files are 3D images, which traditionally were always marked unused. These images are ''actually'' unused, as they have no transclusions.\n'

        for file in sorted(language_files):
          output += f'* [[:File:{file}]]\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_unused_files.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

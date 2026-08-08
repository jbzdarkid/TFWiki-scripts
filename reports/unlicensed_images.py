from .utils import time_and_date
from wikitools import wiki
from wikitools.page import Page

verbose = False

def main(w):
  image_templates = [
    '3D viewer', # 3D models
    'Achievement image', # Transcludes ExtractTF2
    'ArtworkTF2',
    'ArtworkTF2-Pre',
    'AudioTF2',
    'CC',
    'ExtractTF2',
    'FAL',
    'FairUse',
    'Fairuse',
    'GDFL',
    'GPL',
    'LGPL',
    'PD',
    'PD-self',
    'QTF image',
    'ScreenshotTF2',
    'Steam mod content',
    'TFC image',
    'Trademark',
    'Valve content',
    'Valve content/game',
  ]

  all_files = {}
  for file in w.get_all_pages(namespaces = ['File']):
    all_files[file] = []

  if verbose:
    print(f'Found {len(all_files)} files')

  non_files_with_transclusions = []

  for template in image_templates:
    for file in Page(w, f'Template:{template}').get_transclusions(namespaces=['*']):
      if file not in all_files:
        non_files_with_transclusions.append(file)
        all_files[file] = [template]
      else:
        all_files[file].append(template)

  if verbose:
    print('Processed all templates')

  files_with_multiple_templates = [file for file, templates in all_files.items() if len(templates) > 1]
  files_with_no_template =        [file for file, templates in all_files.items() if len(templates) == 0]

  output = """\
{{{{DISPLAYTITLE: {count} files with incorrect licensing}}}}
Found '''<onlyinclude>{count}</onlyinclude>''' files which have an incorrect licensing. Data as of {date}.
__TOC__
""".format(
  count=len(non_files_with_transclusions) + len(files_with_multiple_templates) + len(files_with_no_template),
  date=time_and_date())

  output += '== Non-files with file license templates ==\n'
  for page in non_files_with_transclusions:
    output += f'* [[:{page}]]\n'

  output += '== Files with >1 license template ==\n'
  for file in files_with_multiple_templates:
    output += f'* [[:{file}]]\n'

  output += '== Files with no license templates ==\n'
  for file in files_with_no_template:
    output += f'* [[:{file}]]\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_unlicensed_images.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

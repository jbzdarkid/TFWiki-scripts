from .utils import time_and_date

from wikitools import wiki
from wikitools.page import Page

from . import unlicensed_images

verbose = False

def check_for_redirect(page):
  text = page.get_wiki_text()
  if not text:
    return f'Page {page.title} does not exist\n'
  if '#redirect' in text.lower():
    return f'Page {page.title} is a redirect\n'
  return ''

def main(w):
  output = ''

  output += '  reports/unlicensed_images\n'
  for title in unlicensed_images.image_templates:
    output += check_for_redirect(Page(w, 'Template:' + title))

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_meta_redirects.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

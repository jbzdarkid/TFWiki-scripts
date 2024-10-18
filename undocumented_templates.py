from re import search, sub
from utils import pagescraper_queue, plural, time_and_date, whatlinkshere
from wikitools import wiki
from wikitools.page import Page

verbose = False

def pagescraper(page, badpages):
  page_text = page.get_wiki_text()
  page_visible = sub('<includeonly>.*?</includeonly>', '', page_text)
  if len(page_text) == 0:
    return # Empty templates (usually due to HTTP failures)
  elif '{{tlx|' in page_visible or '{{tl|' in page_visible:
    return # Page has example usages
  elif search('{{([Dd]oc begin|[Tt]emplate doc|[Dd]ocumentation|[Ww]ikipedia doc|[dD]ictionary/wrapper)}}', page_visible):
    return # Page uses a documentation template
  elif '{{{' not in page_text:
    return # Page does not have any arguments 
  elif not search('{{{[a-zA-Z0-9]+}}}', page_visible):
    return # All of the arguments have defaults

  count = page.get_transclusion_count()
  if count > 0:
    if verbose:
      print(f'Page {page.title} does not transclude a documentation template and has {count} backlinks')
    badpages.append([count, page.title])

def main(w):
  navbox_templates = []
  navbox = Page(w, 'Template:Navbox')
  for page in navbox.get_transclusions(namespaces=['Template']):
    if page.title.lower().startswith('template:navbox'):
      continue # Exclude alternative navbox templates
    if page.title.lower().endswith('sandbox'):
      continue # Sandboxes link to pages but shouldn't be used
    if 'navbox' not in page.get_wiki_text().lower():
      continue # Some template pages actually *use* other navboxes, but are not one themselves.
    navbox_templates.append(page.title)

  badpages = []
  with pagescraper_queue(pagescraper, badpages) as page_q:
    for page in w.get_all_templates():
      if '/' in page.title:
        continue # Don't include subpage templates like Template:Dictionary or Template:PatchDiff
      elif page.title[:13] == 'Template:User':
        continue # Don't include userboxes.
      elif page.title in navbox_templates:
        continue # Don't include navboxes, they are self-documenting.
      page_q.put(page)

  badpages.sort(key=lambda s: (-s[0], s[1]))
  output = """\
{{{{DISPLAYTITLE:{count} templates without documentation}}}}
There are <onlyinclude>{count}</onlyinclude> templates which are in use but are undocumented. Please either add a <nowiki><noinclude></nowiki> section with a usage guide, or make use of {{{{tl|Documentation}}}}. Data as of {date}.

""".format(
      count=len(badpages),
      date=time_and_date())

  for count, title in badpages:
    output += f'* [[{title}|]] ([{whatlinkshere(title, count, hidelinks=1)} {plural.uses(count)}])\n'
  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_undocumented_templates.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

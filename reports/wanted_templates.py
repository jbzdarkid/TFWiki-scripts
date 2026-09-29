from collections import defaultdict
from .utils import plural, time_and_date, whatlinkshere
from wikitools import wiki
from wikitools.page import Page

verbose = False
NAMESPACES = ['Main', 'TFW', 'Help', 'File', 'Category']

def main(w):
  wanted_templates = defaultdict(list)
  for template in w.get_all_wanted_templates():
    for page in Page(w, template).get_transclusions(namespaces=NAMESPACES):
      if page.title.startswith('Team Fortress Wiki:Discussion'):
        continue # People are allowed to talk about nonexistent templates
      if page.basename.endswith(' (custom mission)'):
        continue # These pages are generally poorly translated

      wanted_templates[template].append(page)

  output = """\
{{{{DISPLAYTITLE: {count} wanted templates}}}}
List of all <onlyinclude>{count}</onlyinclude> broken template transclusions (usually due to typos or missing dictionary entries). Data as of {date}.

== List ==\n""".format(
    count=sum(len(v) for v in wanted_templates.values()),
    date=time_and_date())

  for template in sorted(wanted_templates.keys()):
    output += f'== [[{template}]] ==\n'
    for page in sorted(wanted_templates[template]):
      output += f'* [[{page.title}]]\n'

  return output

if __name__ == '__main__':
  import os
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php', user_agent=os.environ['USER_AGENT'])
  with open('wiki_wanted_templates.txt', 'w', encoding='utf-8') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

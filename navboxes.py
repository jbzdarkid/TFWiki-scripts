from utils import pagescraper_queue, time_and_date
from wikitools import wiki
from wikitools.page import Page

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']
NAMESPACES = ['Main', 'TFW', 'Help', 'File', 'Template']

excluded_templates = [
  # Class navs have way too many items in them to be useful
  # 'Template:Scout Nav',
  # 'Template:Soldier Nav',
  # 'Template:Pyro Nav',
  # 'Template:Demoman Nav',
  # 'Template:Heavy Nav',
  # 'Template:Engineer Nav',
  # 'Template:Medic Nav',
  # 'Template:Sniper Nav',
  # 'Template:Spy Nav',
  # The class hat tables aren't really navboxes, even though they call {{Navbox}}
  'Template:Scout class hat table',
  'Template:Soldier class hat table',
  'Template:Pyro class hat table',
  'Template:Demoman class hat table',
  'Template:Heavy class hat table',
  'Template:Engineer class hat table',
  'Template:Medic class hat table',
  'Template:Sniper class hat table',
  'Template:Spy class hat table',
  'Template:All class hat table',
  'Template:Misc items table',
  # These are also not navboxes
  'Template:Information',
  'Template:Main Page (Classic) layout',
  'Template:Main Page layout',
  'Template:Mann Vs Machine Nav/no category',
  'Template:Mvm Missions Nav/missioncategoryonly',
  'Template:Patch layout',
  # These are navbox-esque but generate too many false positives.
  'Template:CentralDiscussion',
  'Template:Chinese Editor Team',
]

excluded_pages = {
  # Links for clarification reasons, which aren't really part of the navbox
  'Template:ClassicSniperNav': ['Team Fortress'],
  'Template:Haunted Halloween Special Nav': ['Non-player characters'],
  'Template:Scream Fortress Nav': ['Non-player characters'],

  # Just because there *were* arena/koth/5cp maps in an update doesn't mean we should link it from [[Arena]]
  'Template:Halloween Map Nav': ['Arena', 'King of the Hill', 'Payload', 'Player Destruction', 'Special Delivery (game mode)'],
  'Template:Two Cities Update Nav': ['Control Point (game mode)', 'Items'],
  'Template:Smissmas Map Nav': ['Capture the Flag', 'Control Point (game mode)', 'King of the Hill', 'Payload', 'Player Destruction'],

  # The major updates which introduced certain classes' achievements aren't really topical.
  'Template:Scout Update Nav': ['Scout achievements', 'Obtaining Scout achievements'],
  'Template:War Update Nav': ['Soldier achievements', 'Obtaining Soldier achievements', 'Demoman achievements', 'Obtaining Demoman achievements'],
  'Template:Pyro Update Nav': ['Pyro achievements', 'Obtaining Pyro achievements'],
  'Template:Heavy Update Nav': ['Slowdown', 'Heavy achievements', 'Obtaining Heavy achievements'],
  'Template:Engineer Update Nav': ['Buildings', 'Engineer achievements', 'Obtaining Engineer achievements'],
  'Template:Goldrush Update Nav': ['Medic achievements', 'Obtaining Medic achievements'],
  'Template:Sniper Vs Spy Update Nav': ['Sniper achievements', 'Obtaining Sniper achievements', 'Spy achievements', 'Obtaining Spy achievements'],
  'Template:Two Cities Update Nav': ['Mann vs. Machievements', 'Obtaining Mann vs. Machievements'],

  # The major updates which had new soundtracks aren't really topical.
  'Template:Scream Fortress Nav': 'Team Fortress 2 Official Soundtrack',
  'Template:Meet Your Match Update Nav': 'Team Fortress 2 Official Soundtrack',
  'Template:Jungle Inferno Update Nav': 'Team Fortress 2 Official Soundtrack',
}


def pagescraper(navbox, navbox_templates):
  links = []
  transclusions = []
  for namespace in NAMESPACES:
    links.extend(navbox.get_links(namespace=namespace))
    transclusions.extend(navbox.get_transclusions(namespace=namespace))
  navbox_templates[navbox.title] = [
    set(link.title for link in links),
    set(trans.title for trans in transclusions),
  ]
  if verbose:
    print(f'Navbox {navbox.title} links to {len(links)} pages and is transcluded by {len(transclusions)} pages')

def main(w):
  navbox_templates = {}
  template_navbox = Page(w, 'Template:Navbox')

  with pagescraper_queue(pagescraper, navbox_templates) as navboxes:
    for page in template_navbox.get_transclusions(namespace='Template'):
      if page.title.lower().startswith('template:navbox'):
        continue # Exclude alternative navbox templates
      if page.title.lower().endswith('sandbox'):
        continue # Sandboxes link to pages but shouldn't be used
      if 'navbox' not in page.get_wiki_text().lower():
        continue # Some template pages actually *use* other navboxes, but are not one themselves.
      if page.title in excluded_templates: # Some templates are simply too large to be put on every page.
        continue

      navboxes.put(page)

  if verbose:
    print(f'Found {len(navbox_templates)} navbox templates')

  missing_navboxes = {template: [] for template in navbox_templates}
  extra_navboxes = {template: [] for template in navbox_templates}
  count = 0
  count2 = 0
  for page in w.get_all_pages(namespaces=NAMESPACES):
    expected_navboxes = 0
    page_missing_navboxes = []
    page_extra_navboxes = []

    for template in navbox_templates:
      links, transclusions = navbox_templates[template]

      basename, _, lang = page.title.rpartition('/')
      if lang not in LANGS:
        lang = 'en'
        basename = page.title

      # Some additional manual removals
      if basename in excluded_pages.get(template, []):
        continue

      # Each page that the navbox links to should also transclude the template.
      if basename in links:
        expected_navboxes += 1
        if page.title not in transclusions:
          page_missing_navboxes.append(template)

      # Each page that transcludes the navbox should be linked from the navbox
      if basename in transclusions:
        if page.title not in links:
          page_extra_navboxes.append(template)

    # Some pages are too generic, and are linked to by many navboxes. If a page would have more than 5 navboxes,
    # don't bother reporting about it -- editors will have to use best judgement.
    if expected_navboxes > 5:
      continue

    if page_missing_navboxes:
      count += 1
      for template in page_missing_navboxes:
        missing_navboxes[template].append(page)

    if page_extra_navboxes:
      count2 += 1
      for template in page_extra_navboxes:
        extra_navboxes[template].append(page)

  output = """\
{{{{DISPLAYTITLE:{total_count} pages missing navbox templates}}}}
There are <onlyinclude>{total_count}</onlyinclude> pages which have too many / too few navboxes. {count} pages are short on navboxes; {count2} pages have too many. Data as of {date}.

""".format(
      total_count=count+count2,
      count=count,
      count2=count2,
      date=time_and_date())

  output += '== Missing navboxes ==\n'
  for template in sorted(missing_navboxes.keys()):
    if len(missing_navboxes[template]) == 0:
      continue

    output += '=== {{tl|%s}} (%d) ===\n' % (template.replace('Template:', ''), len(missing_navboxes[template]))
    for page in sorted(missing_navboxes[template]):
      output += f'* [{page.get_edit_url()} {page.title}] does not transclude {template}\n'

  output += '== Extraneous navboxes ==\n'
  for template in sorted(extra_navboxes.keys()):
    if len(extra_navboxes[template]) == 0:
      continue

    output += '=== {{tl|%s}} (%d) ===\n' % (template.replace('Template:', ''), len(extra_navboxes[template]))
    for page in sorted(extra_navboxes[template]):
      output += f'* [{page.get_edit_url()} {page.title}] is not linked from {template}\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_navboxes.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

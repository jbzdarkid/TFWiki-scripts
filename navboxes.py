from utils import time_and_date
from wikitools import wiki
from wikitools.page import Page

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']
NAMESPACES = ['Main', 'TFW', 'Help', 'File', 'Template']

def main(w):
  excluded_templates = [
    # Class navs have way too many items in them to be useful
    'Template:Scout Nav',
    'Template:Soldier Nav',
    'Template:Pyro Nav',
    'Template:Demoman Nav',
    'Template:Heavy Nav',
    'Template:Engineer Nav',
    'Template:Medic Nav',
    'Template:Sniper Nav',
    'Template:Spy Nav',
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


  navbox_templates = {}
  navbox = Page(w, 'Template:Navbox')
  for page in navbox.get_transclusions(namespace='Template'):
    if page.title.lower().startswith('template:navbox'):
      continue # Exclude alternative navbox templates
    if page.title.lower().endswith('sandbox'):
      continue # Sandboxes link to pages but shouldn't be used
    if 'navbox' not in page.get_wiki_text().lower():
      continue # Some template pages actually *use* other navboxes, but are not one themselves.
    if page.title in excluded_templates: # Some templates are simply too large to be put on every page.
      continue

    links = []
    transclusions = []
    for namespace in NAMESPACES:
      links.extend(page.get_links(namespace=namespace))
      transclusions.extend(page.get_transclusions(namespace=namespace))
    navbox_templates[page.title] = [
      set(link.title for link in links),
      set(trans.title for trans in transclusions),
    ]
    if verbose:
      print(f'Navbox {page.title} links to {len(navbox_templates[page.title][0])} pages and is transcluded by {len(navbox_templates[page.title][1])} pages')

  if verbose:
    print(f'Found {len(navbox_templates)} navbox templates')

  missing_navboxes = {template: [] for template in navbox_templates}
  count = 0
  for page in w.get_all_pages(namespaces=NAMESPACES):
    expected_navboxes = 0
    page_missing_navboxes = []

    for template in navbox_templates:
      links, transclusions = navbox_templates[template]

      basename, _, lang = page.title.rpartition('/')
      if lang not in LANGS:
        lang = 'en'
        basename = page.title

      # Some additional manual removals
      if basename in excluded_pages.get(template, []):
        continue

      if basename in links:
        expected_navboxes += 1
        if page.title not in transclusions:
          page_missing_navboxes.append(template)

    if page_missing_navboxes and expected_navboxes < 5: # Some pages are too generic to have a meaningful list of navboxes
      count += 1
      for template in page_missing_navboxes:
        missing_navboxes[template].append(page)

  output = """\
{{{{DISPLAYTITLE:{count} pages missing navbox templates}}}}
There are <onlyinclude>{count}</onlyinclude> pages which are part of a navbox but do not include said navbox. Data as of {date}.

""".format(
      count=count,
      date=time_and_date())

  for template in sorted(missing_navboxes.keys()):
    if len(missing_navboxes[template]) == 0:
      continue

    output += '== {{tl|%s}} (%d) ==\n' % (template.replace('Template:', ''), len(missing_navboxes[template])
    for page in sorted(missing_navboxes[template]):
      output += f'* [{page.get_edit_url()} {page.title}] does not transclude {template}\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_navboxes.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

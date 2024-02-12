from utils import time_and_date
from wikitools import wiki

verbose = False
LANGS = ['ar', 'cs', 'da', 'de', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sv', 'tr', 'zh-hans', 'zh-hant']

def main(w):
  # Some english pages were merged together into one, larger page since they were very repetitive.
  # In these cases, it's not an instance of overtranslation, the translation is just out of date.
  pages_which_were_merged = [
    # BlapBash
    "Blapature Co. Backer",
    "Blapature Co. Benefactor",
    "Blapature Co. Contributor",
    "Blapature Co. Supporter",
    "BlapBash Advocator 2022",
    "BlapBash Backer 2019",
    "BlapBash Backer 2021",
    "BlapBash Backer 2022",
    "BlapBash Benefactor 2019",
    "BlapBash Benefactor 2021",
    "BlapBash Benefactor 2022",
    "BlapBash Supporter 2019",
    "BlapBash Supporter 2021",
    "BlapBash Supporter 2022",

    # Hugs.tf
    "Heartfelt Hug",
    "Heartfelt Hero",

    # Jingle Jam
    "Duncan's Kindhearted Kisser",
    "Hannah's Altruistic Aspect",
    "Heart of Gold",
    "Honeydew's Charitable Countenance",
    "Israphel's Eleemosynary Expression",
    "Mandrew's Munificent Mug",
    "Sips' Selfless Simulacrum",
    "Sjin's Generous Guise",
    "Thought that Counts",
    "Xephos' Philanthropic Physiognomy",

    # Operation Canteen Crasher
    "Canteen Crasher Bronze Ammo Medal 2018",
    "Canteen Crasher Gold Uber Medal 2018",
    "Canteen Crasher Iron Recall Medal 2018",
    "Canteen Crasher Platinum Crit Medal 2018",
    "Canteen Crasher Platinum Krit Medal 2018",
    "Canteen Crasher Rust Starter Medal 2018",
    "Canteen Crasher Silver Building Medal 2018",
    "Canteen Crasher Wood Starter Medal 2018",

    # Operation Titanium Tank
    "Replica Titanium Tank 2020",
    "Titanium Tank Chromatic Cardioid 2020",
    "Titanium Tank Gilded Giver 2020",
    "Titanium Tank Participant Medal 2017",
    "Titanium Tank Participant Medal",

    # TF2Maps 72hr Jam
    "TF2Maps 72hr TF2Jam Participant",
    "TF2Maps 72hr TF2Jam Summer Participant",
    "TF2Maps 72hr TF2Jam Winter Participant",
    "TF2Maps Charitable Heart 2017",
    "TF2Maps Charitable Heart 2021",
    "TF2Maps Charitable Heart",
    "TF2Maps Ray of Sunshine 2018",
    "TF2Maps Ray of Sunshine 2019",
    "TF2Maps Ray of Sunshine 2020",
    "TF2Maps Ray of Sunshine 2022",
    "TF2Maps Ray of Sunshine",
    "Tournament Medal - TF2Maps 72hr TF2Jam Participant",

    # Tournament Medal - LBTF2 6v6
    "LBTF2 6v6 3rd Place Season 9",
    "LBTF2 6v6 1st Place Season 10",
    "LBTF2 6v6 3rd Place Season 9",
    "LBTF2 6v6 2nd Place Season 10",
    "LBTF2 6v6 3rd Place Season 9",
    "LBTF2 6v6 3rd Place Season 10",
    "LBTF2 6v6 Access 1st Place",
    "LBTF2 6v6 Access 2nd Place",
    "LBTF2 6v6 Access 3rd Place",
    "LBTF2 6v6 Access Participant",
    "LBTF2 6v6 Beginner 1st Place",
    "LBTF2 6v6 Beginner 2nd Place",
    "LBTF2 6v6 Beginner 3rd Place",
    "LBTF2 6v6 Beginner Participant",
    "LBTF2 6v6 Central 1st Place",
    "LBTF2 6v6 Central 2nd Place",
    "LBTF2 6v6 Central 3rd Place",
    "LBTF2 6v6 Central Participant",
    "LBTF2 6v6 Elite 1st Place",
    "LBTF2 6v6 Elite 2nd Place",
    "LBTF2 6v6 Elite 3rd Place",
    "LBTF2 6v6 Elite Participant",
    "LBTF2 6v6 Open 1st Place",
    "LBTF2 6v6 Open 2nd Place",
    "LBTF2 6v6 Open 3rd Place",
    "LBTF2 6v6 Open Participant",
    "LBTF2 6v6 Participant Season 9",
    "LBTF2 6v6 Participant Season 10",
    "Tournament Medal - LBTF2 6v6 (Season 10)",
    "Tournament Medal - LBTF2 6v6 (Season 11)",
    "Tournament Medal - LBTF2 6v6 (Season 15)",
    "Tournament Medal - LBTF2 6v6 (Season 16)",
    "Tournament Medal - LBTF2 6v6 Tournament (Season 9)",
    "Tournament Medal - LBTF2 6v6 Tournament (Season 10)",
    "Tournament Medal - LBTF2 6v6 Tournament (Season 11)",
    "Tournament Medal - LBTF2 6v6 Tournament (Season 12)",
    "Tournament Medal - LBTF2 6v6 Tournament (Season 13)",
    "Tournament Medal - LBTF2 6v6 Tournament (Season 14)",
    "Tournament Medal - LBTF2 Tournament (Season 9)",

    # Workshop Wonderland
    'Gift of Giving 2016', 
    'Gift of Giving',
    'Special Snowflake 2016',
    'Special Snowflake',
    'Spectral Snowflake',
  ]

  all_pages = {language: set() for language in LANGS}
  all_english_pages = set()
  for page in w.get_all_pages(namespaces=['Main', 'Help', 'Category']):
    if page.lang == 'en':
      all_english_pages.add(page.title)
    elif page.basename in pages_which_were_merged:
      pass
    else:
      all_pages[page.lang].add(page.basename)

  overtranslated = {language: set() for language in LANGS}
  count = 0

  for language in LANGS:
    for page in sorted(all_pages[language]):
      if page not in all_english_pages:
        if verbose:
          print(f'Page {page}/{language} has no english equivalent')
        overtranslated[language].add(page)
        count += 1

  output = """\
{{{{DISPLAYTITLE: {count} pages with no english equivalent}}}}
'''<onlyinclude>{count}</onlyinclude>''' translated articles which do not have a corresponding article in english (only redirects). Data as of {date}.

""".format(
      count=count,
      date=time_and_date())

  for language in LANGS:
    if len(overtranslated[language]) == 0:
      continue

    output += '== {{lang name|name|%s}} ==\n' % language
    for page in sorted(overtranslated[language]):
      output += '* [[%s/%s]] does not have a non-redirect english equivalent: [[%s]]\n' % (page, language, page)

  return output


if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_overtranslated.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

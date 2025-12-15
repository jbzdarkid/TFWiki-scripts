from datetime import datetime, timedelta, UTC
from .utils import pagescraper_queue, time_and_date
from wikitools import wiki

verbose = False
one_month_ago = datetime.now(UTC) - timedelta(days=30)
one_week_ago  = datetime.now(UTC) - timedelta(days=7)
KNOWN_BOTS = ['WelcomeBOT'] # We only need to list bots which post to talkpages.

def pagescraper(page, active_one_week, active_one_month):
  if verbose:
    print(f'Fetching revisions for {page}')
  weekly_users = set()
  monthly_users = set()
  for revision in page.get_revisions(one_month_ago):
    if revision['user'] in KNOWN_BOTS:
      continue
    if revision['timestamp'] > one_week_ago:
      weekly_users.add(revision['user'])
      monthly_users.add(revision['user'])
    elif revision['timestamp'] > one_month_ago:
      monthly_users.add(revision['user'])

  # A discussion is considered 'active' if it has any user in the past week, or more than 3 users in the past month.
  if len(weekly_users) >= 1:
    active_one_week.append(page)
  elif len(monthly_users) >= 3:
    active_one_month.append(page)

def main(w):
  namespaces = [ns for ns in w.namespaces if 'talk' in ns.lower()]

  recent_pages = set()
  for page in w.get_recent_changes(one_month_ago, namespaces=namespaces):
    recent_pages.add(page)
  if verbose:
    print(f'Found {len(recent_pages)} recently modified talkpages in the past month')

  active_one_week = []
  active_one_month = []
  with pagescraper_queue(pagescraper, active_one_week, active_one_month) as pages:
    for page in recent_pages:
      pages.put(page)
  if verbose:
    print(f'Found {len(active_one_week)} active discussions this week')
    print(f'Found {len(active_one_month)} active discussions this month')

  output = """\
{{{{DISPLAYTITLE: {count} active discussions}}}}
There are '''<onlyinclude>{count}</onlyinclude>''' active discussions as of {date}.

""".format(
    count=len(active_one_week + active_one_month),
    date=time_and_date())

  active_one_week.sort()
  output += '== Active talk pages in the past week ==\n'
  for page in active_one_week:
    output += f'* [[{page}]]\n'

  active_one_month.sort()
  output += '== Active talk pages in the past month ==\n'
  for page in active_one_month:
    output += f'* [[{page}]]\n'

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_all_articles.txt', 'w') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

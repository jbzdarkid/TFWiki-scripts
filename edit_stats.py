from __future__ import division
from datetime import date, datetime
from operator import itemgetter
from time import strftime, strptime, gmtime
from wikitools import wiki

verbose = False
NUMYEARS = date.today().year-2010 + 1 # 2014 - 2010 + 1 = 5 (years)

def userEditCount(sortedList, nlower, nupper=None):
  count = 0
  for user in sortedList:
    if nlower <= user['editcount']:
      if nupper is None or user['editcount'] <= nupper:
        count += 1
  return count

def addTableRow(sortedList, nlower, nupper=None):
  if verbose:
    print("Adding users with edit count", nlower, "-", nupper)
  count = userEditCount(sortedList, nlower, nupper)
  if nupper is None:
    return """|-
| {nlower}+
| {{{{Chart bar|{count}|max={max}}}}}
| {percentage}%""".format(nlower = nlower,
             count = count,
             max = len(sortedList),
             percentage = round(100 * float(count) / len(sortedList), 2)
             )
  else:
    return """|-
| {nlower} - {nupper}
| {{{{Chart bar|{count}|max={max}}}}}
| {percentage}%""".format(nlower = nlower,
             nupper = nupper,
             count = count,
             max = len(sortedList),
             percentage = round(100 * float(count) / len(sortedList), 2)
             )

def monthName(n):
  return [
    None,
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ][n]

def addTimeData(timeSortedList):
  if verbose:
    print("Adding user signups")
  timeRange = [[0]*12 for i in range(NUMYEARS)] # timeRange[year][month]
  for user in timeSortedList:
    time = user['registration']
    timeRange[int(time[:4])-2010][int(time[5:7])-1] += 1 # 2013-05 -> year 3, month 4
  runningTotal = 0
  output = ""
  for year in range(2010, 2010+NUMYEARS):
    for month in range(1, 13):
      if year == date.today().year and month == date.today().month:
        break # We've reached the present, so current data is incorrect and future data is blank.
      numUsers = timeRange[year-2010][month-1]
      if numUsers == 0:
        continue # No data for given time period
      runningTotal += numUsers
      output += """|-
| data-sort-value="{year}-{month}" | {monthName} {year}
| {{{{Chart bar|{numUsers}|max=3500}}}}
| {total}\n""".format(numUsers = numUsers,
       month = "%02d" % month,
       monthName = monthName(month),
       year = year,
       total = runningTotal)
  return output

def addTopUsers(w, sortedList, count):
  if verbose:
    print("Adding top", count, "users")

  bots = list(w.get_all_bots())
  output = ""
  i = 0
  while i < count:
    user = sortedList[i]
    username = user['name']
    usereditcount = user['editcount']
    userregistration = user['registration']
    userlink = 'User:'+username
    place = i+1 # List is indexed 0-99, editors are indexed 1-100
    if username in bots:
      place = "<small>''BOT''</small>"
      del sortedList[i]
      i -= 1
    userstarttime = strptime(userregistration, r'%Y-%m-%dT%H:%M:%SZ')
    timedelta = (datetime.now() - datetime(*userstarttime[:6])).days
    editsperday = round(float(usereditcount) / timedelta, 2)
    output += u"""|-
  | {place} || [[{userlink}|{username}]] || {editcount} || {editday}
  | data-sort-value="{sortabledate}" | {date}\n""".format(
        place = place, # List is indexed 0-99, editors are indexed 1-100
        userlink = userlink,
        username = username,
        editcount = usereditcount,
        editday = str(editsperday),
        sortabledate = strftime(r'%Y-%m-%d %H:%M:00', userstarttime),
        date = strftime(r'%H:%M, %d %B %Y', userstarttime),
        )
    i += 1
  return output

def main(w):
  usersList = list(w.get_all_users())

  sortedList = sorted(usersList, key=itemgetter('editcount'), reverse=True)
  timeSortedList = sorted(usersList, key=itemgetter('registration'))

  output = """User edits statistics. Data accurate as of """ + str(strftime(r'%H:%M, %d %B %Y', gmtime())) + """ (GMT).
;Note: All data excludes registered users with no edits.

== Edit count distribution ==
{| class="wikitable grid sortable plainlinks" style="text-align: center"
! class="header" width="30%" | Number of edits
! class="header" width="50%" | Users
! class="header" width="20%" | Percentage of users
""" + addTableRow(sortedList, 1, 10) + """
""" + addTableRow(sortedList, 11, 100) + """
""" + addTableRow(sortedList, 101, 1000) + """
""" + addTableRow(sortedList, 1001, 5000) + """
""" + addTableRow(sortedList, 5001) + """
|}

== User signups ==
{| class="wikitable grid sortable plainlinks" style="text-align:center"
! class="header" width="30%" | Date
! class="header" width="50%" | Signups
! class="header" width="20%" | Total number of users
""" + addTimeData(timeSortedList) + """
|}

== Top 100 editors ==
{| class="wikitable grid sortable"
! class="header" data-sort-type="number" | #
! class="header" | User
! class="header" | Edit count
! class="header" | Edits per day
! class="header" | Registration date
""" + addTopUsers(w, sortedList, 100) + """
|}"""

  return output

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  with open('wiki_edit_stats.txt', 'w', encoding='utf-8') as f:
    f.write(main(w))
  print(f'Article written to {f.name}')

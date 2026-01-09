import re

from wikitools.page import Page



## Extracted from CoreSource (and cleaned up in many cases)


regex_cache = {}
def compileRegex(regex, flags=re.IGNORECASE):
  global regex_cache
  regex = u(regex)
  if regex not in regex_cache:
    regex_cache[regex] = re.compile(regex, flags)
  return regex_cache[regex]

def u(s):
  return s # I think we don't need this? TODO, I guess.

def addWhitelistPage(*args):
  pass

def editPage(p, content, summary='', minor=True, bot=True, nocreate=True):
  print(f'Attempted to edit page {p} with content:\n{content}')
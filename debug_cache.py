from wikitools.wiki import Wiki

w = Wiki('https://wiki.teamfortress.com/w/api.php')

if len(sys.argv) > 1:
  print(w.page_text_cache[sys.argv[1]])
  print(w.page_text_cache['metadata'][sys.argv[1]])
else:
  print(w.page_text_cache['metadata'])


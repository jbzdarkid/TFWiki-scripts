import sys
from datetime import datetime, timezone

from wikitools.file_dict import FileDict

# Pure offline inspection of the on-disk cache state for a given page.
# Does NOT hit the wiki -- it just reads the GH Actions cache restored on disk.
# Compares the current `cache_valid` logic against the previous (buggy) variant
# that defaulted `last_fetched` to "now" and therefore always served stale files
# when the metadata entry was missing.

def now_default(data):
  return data.get('last_fetched', datetime.now(timezone.utc).timestamp())

def zero_default(data):
  return data.get('last_fetched', 0)

def ts(value):
  if not value:
    return 'never'
  return datetime.fromtimestamp(value, timezone.utc).isoformat()

def inspect(label, cache, key):
  data = cache.metadata.get(key)
  path = cache._path(key)
  file_exists = path.exists()
  file_size = path.stat().st_size if file_exists else 0

  last_modified = (data or {}).get('last_modified', 0)
  old_fetched = now_default(data or {})
  new_fetched = zero_default(data or {})

  print(f'[{label}]  metadata={data}')
  print(f'[{label}]  file_exists={file_exists}  file_size={file_size}  path={path}')
  print(f'[{label}]  last_modified={ts(last_modified)}')
  print(f'[{label}]  old cache_valid (buggy "default=now"): {old_fetched > last_modified}  (last_fetched={ts(old_fetched)})')
  print(f'[{label}]  new cache_valid (fixed "default=0"):   {new_fetched > last_modified}  (last_fetched={ts(new_fetched)})')

  if file_exists and not data:
    print(f'[{label}]  >>> GHOST CACHE FILE: data is on disk but metadata is missing.')
    print(f'[{label}]  >>> Old code would have served this stale file; new code refetches.')
  if file_exists and data and old_fetched > last_modified and not (new_fetched > last_modified):
    print(f'[{label}]  >>> Old code would have served stale data; new code refetches.')


page_title = sys.argv[1] if len(sys.argv) > 1 else 'Mad Drip/pt-br'
url_title = page_title.replace(' ', '_')

caches = [
  ('text', FileDict('cache/text')),
  ('html', FileDict('cache/html')),
  ('link', FileDict('cache/link')),
]

print(f'Inspecting cache for {page_title!r} (url_title={url_title!r})')
print('=' * 100)
for label, cache in caches:
  inspect(label, cache, url_title)
  print()

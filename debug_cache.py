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

print('=' * 100)
print('--- Cache-wide health summary ---')
for label, cache in caches:
  total = 0
  modified_only = 0  # has last_modified but no last_fetched (the bug)
  fetched_only = 0   # has last_fetched but no last_modified (never marked stale)
  both = 0
  neither = 0
  stale_under_old = 0  # would be served stale by old buggy default
  stale_under_old_examples = []
  for key, data in cache.metadata.items():
    if key == 'metadata':
      continue
    total += 1
    has_mod = 'last_modified' in data
    has_fetch = 'last_fetched' in data
    if has_mod and has_fetch:
      both += 1
    elif has_mod:
      modified_only += 1
      if cache._path(key).exists():
        stale_under_old += 1
        if len(stale_under_old_examples) < 5:
          stale_under_old_examples.append(key)
    elif has_fetch:
      fetched_only += 1
    else:
      neither += 1
  print(f'[{label}]  total={total}  both={both}  modified_only={modified_only}  fetched_only={fetched_only}  neither={neither}')
  print(f'[{label}]  modified_only AND file_exists (served stale by old code): {stale_under_old}')
  if stale_under_old_examples:
    print(f'[{label}]  examples: {stale_under_old_examples}')
  print()

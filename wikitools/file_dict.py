import atexit
from datetime import datetime, timezone
from json import loads, dumps
from pathlib import Path
from hashlib import sha256

class FileDict:
  """
  A pseudo-dictionary, backed by direct file storage.
  By keeping individual keys' data in separate files, we can reduce memory pressure on python.
  This also allows us to cache the files in question, persisting the dictionary's contents across runs.
  """

  def __init__(self, folder):
    # Copy out the metadata in memory since we'll be reading/writing from it a lot.
    self.root = Path(folder)
    self.root.mkdir(parents=True, exist_ok=True)

    self.metadata = loads(self.get('metadata', '{}'))

    # Register an atexit handler to save the metadata before we shut down.
    atexit.register(self.close)

  def close(self):
    self['metadata'] = dumps(self.metadata)

  def _path(self, key):
    hash = sha256()
    hash.update(key.encode('utf-8'))
    hex = hash.hexdigest()
    return (self.root / hex[:2] / hex).with_suffix('.txt')

  def get(self, key, default, *, subkey=None):
    try:
      return self.__getitem__(key, subkey)
    except KeyError:
      return default

  def __getitem__(self, key, subkey=None):
    if not self.cache_valid(key, subkey):
      return None # Cache has expired for the given key
    if subkey:
      key += '-' + subkey

    try:
      with self._path(key).open('r', encoding='utf-8') as f:
        return f.read()
    except FileNotFoundError as ex:
      raise KeyError(f'Key {key} was not found on disk') from ex

  def set(self, key, value, *, subkey=None):
    self.__setitem__(key, value, subkey)

  def __setitem__(self, key, value, subkey=None):
    if subkey:
      key += '-' + subkey
    if key not in self.metadata: # N.B. we are actually writing an entry in the metadata for itself. Unused atm.
      self.metadata[key] = {}
    self.metadata[key]['last_fetched'] = datetime.now(timezone.utc).timestamp()

    self._path(key).parent.mkdir(exist_ok=True, parents=True)
    with self._path(key).open('w', encoding='utf-8') as f:
      f.write(value)

  def cache_valid(self, key, subkey=None):
    if key == 'metadata':
      return True

    # Look up the last modification time and last time we wrote to the cache.
    # If the data has been modified since we cached it, it is not valid.
    # If any piece of data is missing, assume the cache is invalid.

    # The root key is updated when the data is modified, so it resets with or without a subkey.
    last_modified = self.metadata.get(key, {}).get('last_modified', 0)

    # The subkey is updated when the data is fetched, so it only tracks for this subkey fetch.
    if subkey:
      key += '-' + subkey
    last_fetched = self.metadata.get(key, {}).get('last_fetched', 0)

    return last_fetched > last_modified

  # Evict a cache entry if it's not more recent than |dt|
  # This is a soft eviction (i.e. the file continues to exist).
  # This hypothetically allows callers to get data even if it's expired.
  def set_modified(self, key, dt):
    if key == 'metadata':
      return

    if key not in self.metadata:
      self.metadata[key] = {}
    self.metadata[key]['last_modified'] = dt.timestamp()

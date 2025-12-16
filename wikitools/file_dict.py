import atexit
from datetime import datetime, UTC
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

  def get(self, key, default=None):
    try:
      return self.__getitem__(key)
    except KeyError:
      return default

  def __getitem__(self, key):
    if not self.cache_valid(key):
      return None # Cache has expired for the given key

    try:
      with self._path(key).open('r', encoding='utf-8') as f:
        return f.read()
    except FileNotFoundError as ex:
      raise KeyError(f'Key {key} was not found on disk') from ex

  def __setitem__(self, key, value):
    if key not in self.metadata: # N.B. we are actually writing an entry in the metadata for itself. Unused atm.
      self.metadata[key] = {}
    self.metadata[key]['last_fetched'] = datetime.now(UTC).timestamp()

    self._path(key).parent.mkdir(exist_ok=True, parents=True)
    with self._path(key).open('w', encoding='utf-8') as f:
      f.write(value)

  def cache_valid(self, key):
    if key == 'metadata':
      return True

    # Look up the last modification time and last time we wrote to the cache.
    # If the data has been modified since we cached it, it is not valid.
    # If any piece of data is missing, assume the cache is valid.
    data = self.metadata.get(key, {})
    last_modified = data.get('last_modified', 0)
    last_fetched = data.get('last_fetched', datetime.now(UTC).timestamp())

    return last_fetched > last_modified
    """
    one_month_ago = (datetime.now(UTC) - timedelta(days=30)).timestamp()
    return last_modified < one_month_ago or last_cached > last_modified
    """

  # Evict a cache entry if it's not more recent than |dt|
  # This is a soft eviction (i.e. the file continues to exist).
  # This hypothetically allows callers to get data even if it's expired.
  def set_modified(self, key, dt):
    if key == 'metadata':
      return

    if key not in self.metadata:
      self.metadata[key] = {}
    self.metadata[key]['last_modified'] = dt.timestamp()

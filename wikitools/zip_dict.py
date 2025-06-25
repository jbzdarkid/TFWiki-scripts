import atexit
from datetime import datetime, timedelta
from io import BytesIO
from json import loads, dumps
from readerwriterlock import rwlock
from zipfile import ZipFile, ZIP_DEFLATED

class ZipDict:
  """
  A memory-light dictionary, backed by a zipfile.
  This has poor read/write performance (compared to a raw dict)
  but is very efficient for large caches of repetitive text.
  """

  def __init__(self, filename):
    # Since zipfiles are not multithread-safe, we need a reader/writer lock
    # to allow concurrent access.
    self.lock = rwlock.RWLockFair()
    self.zipfile = ZipFile(filename, 'a', ZIP_DEFLATED, compresslevel=9)

    # Copy out the metadata in memory since we'll be reading/writing from it a lot.
    self.metadata = loads(self.get('metadata', '{}'))
    
    # Register an atexit handler to save the zipfile before we shut down.
    # We used to use __del__ but that can close too late (i.e. while python is actively shutting down).
    atexit.register(self.close)

  def close(self):
    self['metadata'] = dumps(self.metadata)
    self.zipfile.close()

  def __getitem__(self, key):
    if not self.is_valid(key):
      return
  
    with self.lock.gen_rlock():
      with self.zipfile.open(key, 'r') as f:
        return f.read().decode('utf-8')

  def get(self, key, default=None):
    try:
      return self.__getitem__(key)
    except KeyError:
      return default

  def __setitem__(self, key, value):
    if key not in self.metadata: # N.B. we are actually writing an entry in the metadata for itself. Unused atm.
      self.metadata[key] = {}
    self.metadata[key]['last_fetched'] = (datetime.utcnow() - timedelta(hours=1)).timestamp() # Buffer 1 hour for safety.

    with self.lock.gen_wlock():
      with self.zipfile.open(key, 'a') as f:
        print('Writing', key, len(value))
        f.seek(0)
        f.write(value.encode('utf-8'))

  def is_valid(self, key):
    if key == 'metadata':
      return True

    # Look up the last modification time and last time we wrote to the cache.
    # If the data has been modified since we cached it, it is not valid.
    # If any piece of data is missing, assume the cache is valid.
    data = self.metadata.get(key, {})
    last_modified = data.get('last_modified', datetime.fromtimestamp(0))
    last_cached = data.get('last_cached', datetime.utcnow())
    
    return last_cached > last_modified
    
  def set_modified(self, key, dt):
    if key == 'metadata':
      return

    if key not in self.metadata:
      self.metadata[key] = {}
    self.metadata[key]['last_modified'] = dt.timestamp()

if __name__ == '__main__':
  import psutil
  p = psutil.Process()
  print(f'{p.memory_info().rss:_}, {p.memory_info().vms:_}')

  z = ZipDict()
  print(z.get('hello', False))
  z['hello'] = 'world'
  print(z['hello'])

  print(f'{p.memory_info().rss:_}, {p.memory_info().vms:_}')

  redundant_string = open(__file__, 'r').read()
  for i in range(20):
    print(i, f'{p.memory_info().rss:_}, {p.memory_info().vms:_}')
    for j in range(100):
      z[str(i * 100 + j)] = redundant_string * 100

  print(f'{p.memory_info().rss:_}, {p.memory_info().vms:_}')
  del z
  print(f'{p.memory_info().rss:_}, {p.memory_info().vms:_}')

  z = {}
  for i in range(20):
    print(i, f'{p.memory_info().rss:_}, {p.memory_info().vms:_}')
    for j in range(100):
      z[str(i * 100 + j)] = redundant_string * 100

  print(f'{p.memory_info().rss:_}, {p.memory_info().vms:_}')
  del z
  print(f'{p.memory_info().rss:_}, {p.memory_info().vms:_}')




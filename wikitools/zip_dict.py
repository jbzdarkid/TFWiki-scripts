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

  def __del__(self):
    with self.lock.gen_rlock():
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
    self.metadata[key]['last_fetched'] = datetime.utcnow() - timedelta.hours(1) # Buffer 1 hour for safety.

    with self.lock.gen_wlock():
      with self.zipfile.open(key, 'w') as f:
        f.write(value.encode('utf-8'))

  def is_valid(self, key):
    if key == 'metadata':
      return True

    data = self.metadata.get(key, None)
    return data and 'last_fetched' in data and 'last_modified' in data and data['last_fetched'] > data['last_modified']
    
  def set_modified(self, key, time):
    if key == 'metadata':
      return

    if key not in self.metadata:
      self.metadata[key] = {}
    self.metadata[key]['last_modified'] = time

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




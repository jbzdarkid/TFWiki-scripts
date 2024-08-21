from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from readerwriterlock import rwlock

class ZipDict:
  """
  A memory-light dictionary, backed by a zipfile.
  This has poor read/write performance (compared to a raw dict)
  but is very efficient for large caches of repetitive text.
  """

  def __init__(self):
    self.buffer = BytesIO()
    self.zipfile = ZipFile(self.buffer, 'a', ZIP_DEFLATED, compresslevel=9)
    # Since zipfiles are not multithread-safe, we need a reader/writer lock
    # to allow concurrent access.
    self.lock = rwlock.RWLockFair()

  def __del__(self):
    self.zipfile.close()
    del self.buffer # Explicitly clean up the buffer to recover memory

  def __getitem__(self, key):
    with self.lock.gen_rlock():
      with self.zipfile.open(key, 'r') as f:
        return f.read().decode('utf-8')

  def get(self, key, default=None):
    try:
      return self.__getitem__(key)
    except KeyError:
      return default

  def __setitem__(self, key, value):
    with self.lock.gen_wlock():
      with self.zipfile.open(key, 'w') as f:
        f.write(value.encode('utf-8'))


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




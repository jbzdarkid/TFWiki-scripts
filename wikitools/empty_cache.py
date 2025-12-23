class EmptyCache:
  """
  A mock version of the FileDict and ZipDict caches (... I'll make an interface at some point)
  This cache always returns empty and is thus perfect for scenarios where caching is not required.
  """

  def get(self, key, default=None):
    return default

  def __getitem__(self, key):
    raise KeyError('There are no keys in an empty cache')

  def __setitem__(self, key, value):
    pass

  def cache_valid(self, key):
    return False

  def set_modified(self, key, dt):
    pass

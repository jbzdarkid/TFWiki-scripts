from queue import Empty, Queue
from threading import Thread, Event
from time import gmtime, strftime

class meta_plural(type):
  def __getattr__(cls, word):
    if word.endswith('s'):
      word = word[:-1]
    return lambda num: f'1 {word}' if num == 1 else f'{num} {word}s'

class plural(metaclass=meta_plural):
  pass

def time_and_date():
  return strftime(r'%H:%M, %d %B %Y (GMT)', gmtime())

def whatlinkshere(title, count, **kwargs):
  kwargs.setdefault('limit', min(50, count))
  kwargs.setdefault('namespace', 0)
  kwargs.setdefault('hideredirs', 1)
  query = '&'.join(f'{key}={value}' for key, value in kwargs.items())

  return '{{fullurl:Special:WhatLinksHere/%s|%s}}' % (title, query)


class pagescraper_queue:
  def __init__(self, thread_func, *args, num_threads=50):
    self.thread_func = thread_func
    self.thread_func_args = args
    self.num_threads = num_threads

  def __enter__(self):
    self.q = Queue()
    self.done = Event()
    self.threads = []
    self.count = 0
    self.failures = 0
    for _ in range(self.num_threads):
      thread = Thread(target=self.meta_thread_func)
      self.threads.append(thread)
      thread.start()
    return self

  def put(self, obj):
    self.q.put(obj)
    self.count += 1

  def __len__(self):
    return self.count

  def __exit__(self, exc_type, exc_val, traceback):
    self.done.set()
    for thread in self.threads:
      thread.join()
    if self.failures > 5:
      raise Exception(f'There were {self.failures} exceptions thrown during execution')

  def meta_thread_func(self):
    while True:
      try:
        obj = self.q.get(True, 1)
      except Empty:
        if self.done.is_set():
          return
        else:
          continue

      try:
        self.thread_func(obj, *self.thread_func_args)
      except KeyboardInterrupt:
        self.done.set()
        self.q = Queue() # "Clear" the queue
        self.failures = 9999
        return
      except:
        self.failures += 1
        import traceback
        traceback.print_exc()

class pagescraper_queue_single:
  def __init__(self, thread_func, *args):
    self.thread_func = thread_func
    self.thread_func_args = args

  def __enter__(self):
    self.failures = 0
    return self

  def put(self, obj):
    try:
      self.thread_func(obj, *self.thread_func_args)
    except KeyboardInterrupt:
      raise
    except:
      self.failures += 1
      import traceback
      traceback.print_exc()

  def __exit__(self, exc_type, exc_val, traceback):
    if self.failures > 5:
      raise Exception(f'There were {self.failures} exceptions thrown during execution')

if __name__ == '__main__':
  print(f'There are {plural.translations(2)} but only {plural.dogs(1)}')

from queue import Empty, Queue
from threading import Thread, Event

class meta_plural(type):
  def __getattr__(clazz, word):
    if word.endswith('s'):
      word = word[:-1]
    return lambda num: f'1 {word}' if num == 1 else f'{num} {word}s'

class plural(metaclass=meta_plural):
  pass

def whatlinkshere(title, count, **kwargs):
  kwargs.setdefault('limit', min(50, count))
  kwargs.setdefault('namespace', 0)
  kwargs.setdefault('hideredirs', 1)
  query = '&'.join(f'{key}={value}' for key, value in kwargs.items())

  return '{{fullurl:Special:WhatLinksHere/%s|%s}}' % (title, query)


class pagescraper_queue:
  NUM_THREADS = 50

  def __init__(self, thread_func, *args):
    self.q = Queue()
    self.done = Event()
    self.threads = []
    self.thread_func = thread_func
    self.thread_func_args = args

  def __enter__(self):
    for _ in range(PAGESCRAPERS): # Number of threads
      thread = Thread(target=self.meta_thread_func)
      threads.append(thread)
      thread.start()

  def __exit__(self):
    self.done.set()
    for thread in self.threads:
      thread.join()

  def put(self, obj):
    self.q.put(obj)

  def meta_thread_func(self):
    while True:
      try:
        obj = self.get(True, 1)
      except Empty:
        if self.done.is_set():
          return
        else:
          continue

      try:
        self.thread_func(obj, *self.thread_func_args)
      except Exception as e:
        print(e)

if __name__ == '__main__':
  print(f'There are {plural.translations(2)} but only {plural.dogs(1)}')

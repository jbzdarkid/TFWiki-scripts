from datetime import datetime, timedelta
from time import sleep
from wikitools import wiki
from wikitools.page import Page
from .utils import pagescraper_queue

def pagescraper_get(page):
  page.get_revisions(datetime.now() - timedelta(days=30))

def pagescraper_post(page):
  Page(w, 'User:Darkid/Test').edit(page.title, 'testing')

def main(w):
  all_pages = []
  with pagescraper_queue(pagescraper_get, num_threads=64) as pages:
    for page in w.get_all_pages(namespaces=['Main', 'TFW', 'File', 'Template', 'Help', 'Category']):
      all_pages.append(page)
      pages.put(page)

  sleep(10 * 60)

  with pagescraper_queue(pagescraper_post, num_threads=64) as pages:
    for page in all_pages:
      pages.put(page)

if __name__ == '__main__':
  verbose = True
  w = wiki.Wiki('https://wiki.teamfortress.com/w/api.php')
  w.MAX_RETRIES = 0
  main(w)

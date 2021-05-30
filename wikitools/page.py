
class Page:
  def __init__(self, wiki, title):
    self.wiki = wiki
    self.title = title

  def __str__(self):
    return self.title

  def get_wiki_text(self):
    return self.wiki.get('parse', page=self.title, prop='wikitext')['parse']['wikitext']['*']

  def get_transclusion_count(self):
    transclusions = self.wiki.get_with_continue('query', 'embeddedin',
      list='embeddedin',
      eifilterredir='nonredirects', # Filter out redirects
      eilimit='500',
      eititle=self.title,
    )
    return sum(1 for _ in transclusions)


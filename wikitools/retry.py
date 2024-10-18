from urllib3.util import Retry

class StaticRetry(Retry):
  def __init__(self, *args, **kwargs):
    self.static_backoff = kwargs.pop('static_backoff', None)
    super().__init__(*args, **kwargs)

  def get_backoff_time(self, *args, **kwargs):
    if self.static_backoff:
      return self.static_backoff
    return super().get_backoff_time(*args, **kwargs)

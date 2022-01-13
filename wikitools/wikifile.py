from .page import Page

class File(Page):
  def __init__(self, wiki, title):
    super().__init__(wiki, title)

  def upload(self, fileobj, comment=''):
    if fileobj.mode != 'rb':
      print(f'Failed to upload {self.title}, file must be opened in rb (was {fileobj.mode})')
      return
    print(f'Uploading {self.title}...')
    data = self.wiki.post_with_csrf('upload',
      filename=self.url_title,
      file=fileobj.name,
      comment=comment,
      files={'file': (fileobj.name, fileobj, 'multipart/form-data')},
      ignorewarnings=True,
    )

    if 'error' in data:
      print(f'Failed to upload {self.title}:')
      print(data['error'])
    elif data['upload']['result'] != 'Success':
      print(f'Failed to upload {self.title}:')
      print(data['upload'])
    else:
      print(f'Successfully uploaded ' + data['upload']['filename'])

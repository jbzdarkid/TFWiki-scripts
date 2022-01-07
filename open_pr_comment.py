from os import environ
import requests

api_url = 'https://api.github.com/repos/' + environ['GITHUB_REPOSITORY']
headers = {
  'Accept': 'application/vnd.github.v3+json',
  'Authorization': 'Bearer ' + environ['GITHUB_TOKEN'],
}


def make_request(method, path, *args, **kwargs):
  kwargs['headers'] = headers
  r = requests.request(method, f'{api_url}/{path}', *args, **kwargs)
  r.raise_for_status()
  return r.json()


def get_pr_comments(pr, author):
  comments = make_request('GET', f'issues/{pr}/comments')
  return [comment for comment in comments if comment['user']['login'] == author]


def edit_pr_comment(comment_id, new_body):
  return make_request('PATCH', f'issues/comments/{comment_id}', json={'body': new_body})


def create_pr_comment(pr, body):
  return make_request('POST', f'issues/{pr}/comments', json={'body': body})


if __name__ == '__main__':
  if environ['GITHUB_EVENT_NAME'] == 'pull_request':
    comment_body = environ['GITHUB_COMMENT']

    pr = environ['PULL_REQUEST_ID']
    existing_comments = get_pr_comments(pr, 'github-actions[bot]')
    if existing_comments:
      edit_pr_comment(existing_comments[0]['id'], comment_body)
    else:
      create_pr_comment(pr, comment_body)

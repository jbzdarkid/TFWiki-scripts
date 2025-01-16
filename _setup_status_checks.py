import requests
import json

headers = {
  'Accept': 'application/vnd.github+json',
  'Authorization': 'Bearer ghp_token',
  'X-GitHub-Api-Version': '2022-11-28',
}

r = requests.get('https://api.github.com/repos/jbzdarkid/TFWiki-Scripts/commits/lang-incomplete/check-runs')
checks = r.json()['check_runs']

r = requests.get('https://api.github.com/repos/jbzdarkid/TFWiki-scripts/branches/python3/protection', headers=headers)

body = r.json()
body['required_status_checks']['contexts'] = [c['name'] for c in checks]

r = requests.put('https://api.github.com/repos/jbzdarkid/TFWiki-scripts/branches/python3/protection', headers=headers, json=body)
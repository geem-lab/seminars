import os
from pprint import pprint

import requests

if __name__ == "__main__":
    token = os.environ["GITHUB_TOKEN"]
    owner = "geem-lab"
    repo = "seminars"
    query_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    authorization = f"token {token}"

    params = {"state": "open"}
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": authorization,
    }

    gh_session = requests.Session()
    gh_session.auth = (owner, token)

    issues = gh_session.get(query_url, headers=headers, params=params).json()
    pprint(issues)

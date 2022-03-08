import os

import requests
from dateutil import parser as dateutil_parser

if __name__ == "__main__":
    token = os.environ["GITHUB_TOKEN"]
    owner = "geem-lab"
    repo = "seminars"
    query_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    authorization = f"token {token}"

    params = {}  # {"state": "open"}
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": authorization,
    }

    gh_session = requests.Session()
    gh_session.auth = (owner, token)

    issues = gh_session.get(query_url, headers=headers, params=params).json()

    seminars = []
    for issue in issues:
        if issue["title"].startswith("[SEMINAR]"):
            title = issue["title"].replace("[SEMINAR]", "").strip()

            date_marker = "**Date**:"
            body, date = issue["body"].split(date_marker)[:2]
            body = body.rstrip(date_marker).strip()
            date = date.splitlines()[0].strip()
            date = dateutil_parser.parse(date)
            speaker = issue["assignees"][0]["login"]

            seminar = {"title": title, "body": body, "date": date, "speaker": speaker}
            seminars.append(seminar)

    seminars = sorted(seminars, key=lambda s: s["date"])
    for seminar in seminars:
        print(f"- **{seminar['title']}** (*{seminar['date'].strftime('%Y-%m-%d')}*)")
        print(f"  Speaker: @{seminar['speaker']}.")
        print(f"  {seminar['body']}")

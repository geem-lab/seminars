import os
from dataclasses import dataclass
from datetime import datetime

import requests
from dateutil import parser as dateutil_parser
from markdown import markdown


@dataclass
class Seminar:
    title: str
    speaker: str
    description: str
    date: datetime

    def _date_to_markdown(self):
        return f"""
        <p>
            <strong>
                {self.date.strftime('%d/%m/%Y')}
            </strong>
        </p>
        """

    def _title_to_markdown(self):
        return f"""
        <h2>
            {self.title}
        </h2>
        """

    def _speaker_to_markdown(self):
        return f"""
        <p>
            <strong>
                <a href="https://github.com/{self.speaker}">
                    {self.speaker}
                </a>
            </strong>
        </p>
        """

    def _description_to_markdown(self):
        return f"""
        {markdown(self.description)}
        """

    def to_markdown(self):
        return f"""
        <details>
            <summary>
                {self._date_to_markdown()}
                {self._title_to_markdown()}
            </summary>
            {self._speaker_to_markdown()}
            {self._description_to_markdown()}
        </details>
        """


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

            seminar = Seminar(title=title, speaker=speaker, description=body, date=date)
            seminars.append(seminar)

    seminars = sorted(seminars, key=lambda s: s.date)
    for seminar in seminars:
        print(seminar.to_markdown())

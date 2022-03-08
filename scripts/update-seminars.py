import os
from dataclasses import dataclass
from datetime import datetime
from textwrap import dedent

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
        return dedent(
            f"""
            <em>
                <time datetime="{self.date.isoformat()}">
                    {self.date.strftime('%d/%m/%Y')}
                <time>
            </em>
            """
        )

    def _title_to_markdown(self):
        return dedent(
            f"""
            <h2 style="display: inline;">
                {self.title}
            </h2>
            """
        )

    def _speaker_to_markdown(self):
        return dedent(
            f"""
            <p>
                <strong>
                    <a href="https://github.com/{self.speaker}">
                        {self.speaker}
                    </a>
                </strong>
            </p>
            """
        )

    def _description_to_markdown(self):
        return dedent(
            f"""
            {markdown(self.description)}
            """
        )

    def to_markdown(self):
        return dedent(
            f"""
            <details>
                <summary>
                    {self._date_to_markdown()}
                    {self._title_to_markdown()}
                </summary>
                {self._speaker_to_markdown()}
                {self._description_to_markdown()}
            </details>
            """
        )

    DATE_MARKER = "**Date**:"

    @classmethod
    def from_github_issue(cls, issue):
        title = issue["title"].replace("[SEMINAR]", "").strip()

        description, date = issue["body"].split(cls.DATE_MARKER)[:2]
        description = description.rstrip(cls.DATE_MARKER).strip()

        date = date.splitlines()[0].strip()
        date = dateutil_parser.parse(date)

        if issue["assignees"]:
            speaker = issue["assignees"][0]["login"]
        else:
            speaker = issue["user"]["login"]

        return Seminar(title=title, speaker=speaker, description=description, date=date)


@dataclass
class SeminarList:
    seminars: list

    def __post_init__(self):
        self.seminars = sorted(self.seminars, key=lambda seminar: seminar.date)

    def to_markdown(self):
        return "\n".join([seminar.to_markdown() for seminar in self.seminars])

    @staticmethod
    def from_github_issues(issues):
        seminars = [
            Seminar.from_github_issue(issue)
            for issue in issues
            if issue["title"].startswith("[SEMINAR]")
        ]

        return SeminarList(seminars)

    @staticmethod
    def from_github_repo(owner, repo, token=None):
        if token is None:
            token = os.environ["GITHUB_TOKEN"]

        gh_session = requests.Session()
        gh_session.auth = (owner, token)

        params = {}  # {"state": "open"}

        authorization = f"token {token}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": authorization,
        }

        query_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        issues = gh_session.get(query_url, headers=headers, params=params).json()

        return SeminarList.from_github_issues(issues)


if __name__ == "__main__":
    seminars = SeminarList.from_github_repo(owner="geem-lab", repo="seminars")
    print(seminars.to_markdown())

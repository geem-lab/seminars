import os
from dataclasses import dataclass
from datetime import datetime

import requests
from dateutil import parser as dateutil_parser
from markdown import markdown


def tag(tag_name):
    def _tag(*args, **kwargs):
        attrs = " ".join(f'{k}="{v}"' for k, v in kwargs.items())
        contents = "".join(args)
        if attrs:
            return f"<{tag_name} {attrs}>{contents}</{tag_name}>"
        else:
            return f"<{tag_name}>{contents}</{tag_name}>"

    return _tag


em = tag("em")
time = tag("time")
h2 = tag("h2")
p = tag("p")
strong = tag("strong")
a = tag("a")
details = tag("details")
summary = tag("summary")


@dataclass
class Seminar:
    title: str
    speaker: str
    description: str
    date: datetime

    def _date_to_markdown(self):
        return em(time(self.date.strftime("%d/%m/%Y"), datetime=self.date.isoformat()))

    def _title_to_markdown(self):
        return h2(self.title, style="display: inline")

    def _speaker_to_markdown(self):
        return p(
            strong("Speaker: "),
            a(self.speaker, href=f"https://github.com/{self.speaker}"),
        )

    def _description_to_markdown(self):
        return markdown(self.description)

    def to_markdown(self):
        return details(
            summary(
                self._date_to_markdown(),
                self._title_to_markdown(),
                self._speaker_to_markdown(),
            ),
            self._description_to_markdown(),
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

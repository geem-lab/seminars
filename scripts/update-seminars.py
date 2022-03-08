import os
from dataclasses import dataclass
from datetime import datetime

import requests
import dateparser
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
span = tag("span")
li = tag("li")
ul = tag("ul")
small = tag("small")


@dataclass
class Seminar:
    title: str
    speaker: str
    description: str
    date: datetime

    STRFTIME_FORMAT = "%b %-d %Y"

    def _date_to_markdown(self):
        dt = time(
            self.date.strftime(self.STRFTIME_FORMAT), datetime=self.date.isoformat()
        )
        return small(f"{dt}")

    def _title_to_markdown(self):
        return strong(self.title, style="display: inline")

    def _speaker_to_markdown(self):
        return a(f"@{self.speaker}", href=f"https://github.com/{self.speaker}")

    def _description_to_markdown(self):
        return markdown(self.description)

    def to_markdown(self):
        return details(
            summary(
                self._title_to_markdown(),
                " (",
                self._speaker_to_markdown(),
                ", ",
                self._date_to_markdown(),
                ")",
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
        date = dateparser.parse(date)

        if issue["assignees"]:
            speaker = issue["assignees"][0]["login"]
        else:
            speaker = issue["user"]["login"]

        return Seminar(title=title, speaker=speaker, description=description, date=date)


@dataclass
class SeminarList:
    seminars: list[Seminar]

    def __post_init__(self):
        self.seminars = sorted(self.seminars, key=lambda seminar: seminar.date)

    HEADER = """# Seminars

Click on each seminar to see more details.
"""
    FOOTER = """

> Want to add a seminar? Take a look at [the instructions page](/README).
    """

    def to_markdown(self):
        return (
            self.HEADER
            + "".join(seminar.to_markdown() for seminar in self.seminars)
            + self.FOOTER
        )

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

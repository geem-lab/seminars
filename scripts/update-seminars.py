from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

import dateparser
import requests
from markdown import markdown


def request_github_api(query_url: str, owner="geem-lab", token=None) -> dict:
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

    return gh_session.get(query_url, headers=headers, params=params).json()


def tag(tag_name):
    def _tag(*args, **kwargs):
        def _normalize_key(key):
            if key.endswith("_"):
                return key[:-1]
            return key

        attrs = " ".join(f'{_normalize_key(k)}="{v}"' for k, v in kwargs.items())
        contents = "".join(arg for arg in args if arg)

        if attrs and contents:
            return f"<{tag_name} {attrs}>{contents}</{tag_name}>"
        elif attrs:
            return f"<{tag_name} {attrs} />"
        elif contents:
            return f"<{tag_name}>{contents}</{tag_name}>"
        else:
            return f"<{tag_name} />"

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
img = tag("img")


@dataclass
class Seminar:
    title: str
    speaker: dict
    description: str
    date: datetime

    STRFTIME_FORMAT = "%b %-d %Y"

    def __post_init__(self):
        if isinstance(self.speaker, str):
            self.speaker = request_github_api(
                f"https://api.github.com/users/{self.speaker}"
            )

    def _date_to_markdown(self):
        dt = time(
            "📅 ",
            self.date.strftime(self.STRFTIME_FORMAT),
            datetime=self.date.isoformat(),
        )
        return small(strong(dt))

    def _title_to_markdown(self):
        return em(self.title)

    @property
    def speaker_name(self):
        if "name" in self.speaker:
            return self.speaker["name"]
        else:
            return f"@{self.speaker['login']}"

    @property
    def speaker_url(self):
        return f"https://github.com/{self.speaker['login']}"

    def _speaker_name_to_markdown(self):
        return a(self.speaker_name, href=self.speaker_url)

    AVATAR_WIDTH = 128

    def _speaker_avatar_to_markdown(self):
        if "avatar_url" in self.speaker:
            return a(
                img(
                    src=self.speaker["avatar_url"],
                    alt=self.speaker["login"],
                    title=self.speaker_name,
                    align="left",
                    width=self.AVATAR_WIDTH,
                ),
                href=self.speaker_url,
            )

    def _description_to_markdown(self):
        return markdown(self.description)

    def to_markdown(self):
        return details(
            summary(
                self._date_to_markdown(),
                " ",
                self._title_to_markdown(),
                " (",
                self._speaker_name_to_markdown(),
                ")",
            ),
            self._speaker_avatar_to_markdown(),
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
        self.seminars = sorted(
            self.seminars, key=lambda seminar: seminar.date, reverse=True
        )

    HEADER = """# Seminars

Click on each seminar to see more details.

> Want to add a seminar? Take a look at [the instructions page](/seminars/instructions).

"""

    def to_markdown(self):
        return self.HEADER + "".join(seminar.to_markdown() for seminar in self.seminars)

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
        issues = request_github_api(
            f"https://api.github.com/repos/{owner}/{repo}/issues",
            owner=owner,
            token=token,
        )
        return SeminarList.from_github_issues(issues)


if __name__ == "__main__":
    seminars = SeminarList.from_github_repo(owner="geem-lab", repo="seminars")
    print(seminars.to_markdown())

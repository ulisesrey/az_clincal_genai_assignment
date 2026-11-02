"""Parses the procurement policy markdown into Policy Sections keyed by ID, quoted verbatim when cited."""

import re
from dataclasses import dataclass

_HEADING = re.compile(r"^## (\d+)\. (.+)$")
_CLAUSE = re.compile(r"^(\d+\.\d+) (.+)$")


@dataclass(frozen=True)
class Policy:
    text: str
    sections: dict[str, str]


def normalize_section_id(section: str) -> str:
    """'§3.1', ' 3.1.' and '3.1' all name Policy Section 3.1."""
    return section.strip().removeprefix("§").strip().rstrip(".")


def parse_policy(text: str) -> Policy:
    """A numbered heading's text is its title plus the lines under it (e.g. the §3 table) up to its first clause; a clause's text is its line without the number."""
    sections: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in text.splitlines():
        if heading := _HEADING.match(line):
            current = sections.setdefault(heading[1], [heading[2]])
        elif clause := _CLAUSE.match(line):
            current = sections.setdefault(clause[1], [clause[2]])
        elif current is not None:
            current.append(line)
    return Policy(text=text, sections={id: "\n".join(lines).strip() for id, lines in sections.items()})

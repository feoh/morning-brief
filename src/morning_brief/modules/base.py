"""Base interfaces for briefing modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class BriefSection:
    """One rendered section of a morning brief."""

    title: str
    body: str

    def render(self) -> str:
        """Render this section as Discord-friendly Markdown."""

        return f"## {self.title}\n{self.body}".strip()


class BriefingModule(Protocol):
    """Protocol implemented by modules that contribute to a morning brief."""

    name: str

    def build_section(self) -> BriefSection:
        """Build this module's section for the current brief."""
        ...

from __future__ import annotations

from typing import TYPE_CHECKING

from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

if TYPE_CHECKING:
    import xml.etree.ElementTree as etree

    from markdown import Markdown


def _deduplicate_toc(toc: list[dict]) -> None:
    i = 0
    while i < len(toc):
        el = toc[i]
        if el.get("children"):
            _deduplicate_toc(el["children"])
        elif i > 0 and el["name"] == toc[i - 1]["name"]:
            del toc[i]
            continue
        i += 1


class _TocDeduplicatingTreeprocessor(Treeprocessor):
    def run(self, root: etree.Element):
        try:
            toc = self.md.toc_tokens  # type: ignore[attr-defined]
        except AttributeError:
            return
        _deduplicate_toc(toc)


class DeduplicateTocExtension(Extension):
    @classmethod
    def extendMarkdown(cls, md: Markdown) -> None:
        md.treeprocessors.register(
            _TocDeduplicatingTreeprocessor(md), "mkdocstrings_crystal_deduplicate_toc", 4
        )


makeExtension = DeduplicateTocExtension  # noqa: N816

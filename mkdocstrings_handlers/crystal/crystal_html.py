from __future__ import annotations

import collections
import html.parser
import io
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Callable

from markupsafe import Markup, escape

if TYPE_CHECKING:
    _LinkToken = tuple[int, int, str]


class TextWithLinks(collections.UserString):
    """A string with embedded information about which parts of it are links to other items.

    Can be converted to an actual string with `str(obj)` -- or used directly, being a subclass of `str`.

    The link information is currently for internal use only.
    """

    tokens: Sequence[_LinkToken]
    """The list of embedded links."""

    def __init__(self, string, tokens: Sequence[_LinkToken]):
        super().__init__(string)
        self.tokens = tokens

    def __repr__(self) -> str:
        return f"TextWithLinks({self.data!r}, {self.tokens!r})"


def parse_crystal_html(crystal_html: str) -> TextWithLinks:
    parser = _CrystalHTMLHandler()
    parser.feed(crystal_html)
    return TextWithLinks(parser.text.getvalue(), parser.tokens)


def linkify_highlighted_html(
    pygments_html: str, html_tokens: Sequence[_LinkToken], make_link: Callable[[str, str], str]
) -> str:
    pygments_parser = _PygmentsHTMLHandler(html_tokens, make_link)
    pygments_parser.feed(pygments_html)
    return Markup(pygments_parser.html.getvalue())  # noqa: RUF035


class _CrystalHTMLHandler(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.text = io.StringIO()
        self.tokens: list[_LinkToken] = []
        self._link_starts: list[tuple[int, str]] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = next(v for k, v in attrs if k == "href")
            self._link_starts.append((self.text.tell(), self.link_to_path(href)))

    def handle_endtag(self, tag):
        if tag == "a":
            start, link = self._link_starts.pop()
            self.tokens.append((start, self.text.tell(), link))

    def handle_data(self, data):
        self.text.write(data)

    @classmethod
    def link_to_path(cls, href):
        href = href.removesuffix(".html")
        while href.startswith("../"):
            href = href[3:]
        return href.replace("/", "::")


class _PygmentsHTMLHandler(html.parser.HTMLParser):
    def __init__(self, tokens: Iterable[_LinkToken], make_link: Callable[[str, str], str]):
        super().__init__()
        self.tokens = iter(tokens)
        self.make_link = make_link

        self.token = next(self.tokens, None)
        self.pos = 0
        self.html = io.StringIO()
        self.inlink: int | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "span" and self.inlink is None:
            if self.token and self.token[0] <= self.pos:
                self.inlink = self.html.tell()

        if self.inlink is None:
            attrs = "".join(f' {k}="{escape(v)}"' for k, v in attrs)
            self.html.write(f"<{tag}{attrs}>")

    def handle_endtag(self, tag):
        if self.inlink is None:
            self.html.write(f"</{tag}>")

        if tag == "span" and self.inlink is not None:
            if self.token and self.token[1] <= self.pos:
                self.html.seek(self.inlink)
                subhtml = Markup(self.html.read())  # noqa: RUF035
                subhtml = self.make_link(self.token[2], subhtml)
                self.token = next(self.tokens, None)

                self.html.seek(self.inlink)
                self.html.truncate()
                self.html.write(subhtml)
                self.inlink = None

    def handle_data(self, data):
        self.html.write(escape(data))
        self.pos += len(data)

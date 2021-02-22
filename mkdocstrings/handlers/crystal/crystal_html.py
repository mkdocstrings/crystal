import collections
import html.parser
import io
from typing import Callable, List, Sequence, Tuple

from markupsafe import Markup, escape

LinkTokens = Sequence[Tuple[int, int, str]]


class TextWithLinks(collections.UserString):
    """A string with embedded information about which parts of it are links to other items.

    Can be converted to an actual string with `str(obj)` -- or used directly, being a subclass of `str`.

    The link information is currently for internal use only.
    """

    tokens: LinkTokens
    """The list of embedded links."""

    def __init__(self, string, tokens: LinkTokens):
        super().__init__(string)
        self.tokens = tokens

    def __repr__(self) -> str:
        return f"TextWithLinks({self.data!r}, {self.tokens!r})"


def parse_crystal_html(crystal_html: str) -> TextWithLinks:
    parser = _CrystalHTMLHandler()
    parser.feed(crystal_html)
    return TextWithLinks(parser.text.getvalue(), parser.tokens)


def linkify_highlighted_html(
    pygments_html: str, html_tokens: LinkTokens, make_link: Callable[[str, str], str]
) -> str:
    pygments_parser = _PygmentsHTMLHandler(html_tokens, make_link)
    pygments_parser.feed(pygments_html)
    return Markup(pygments_parser.html.getvalue())


class _CrystalHTMLHandler(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = io.StringIO()
        self.tokens: LinkTokens = []
        self._link_starts: List[Tuple[int, str]] = []

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
        if href.endswith(".html"):
            href = href[:-5]
        while href.startswith("../"):
            href = href[3:]
        return href.replace("/", "::")


class _PygmentsHTMLHandler(html.parser.HTMLParser):
    def __init__(self, tokens: LinkTokens, make_link: Callable[[str, str], str]):
        super().__init__()
        self.tokens = tokens
        self.make_link = make_link

        self.pos = 0
        self.html = io.StringIO()
        self.inlink: Optional[int] = None

    def handle_starttag(self, tag, attrs):
        if tag == "span" and self.inlink is None:
            if self.tokens and self.tokens[0][0] <= self.pos:
                self.inlink = self.html.tell()

        if self.inlink is None:
            attrs = "".join(f' {k}="{escape(v)}"' for k, v in attrs)
            self.html.write(f"<{tag}{attrs}>")

    def handle_endtag(self, tag):
        if self.inlink is None:
            self.html.write(f"</{tag}>")

        if tag == "span" and self.inlink is not None:
            if self.tokens and self.tokens[0][1] <= self.pos:
                self.html.seek(self.inlink)
                subhtml = Markup(self.html.read())
                subhtml = self.make_link(self.tokens.pop(0)[2], subhtml)
                self.html.seek(self.inlink)
                self.html.truncate()
                self.html.write(subhtml)
                self.inlink = None

    def handle_data(self, data):
        self.html.write(escape(data))
        self.pos += len(data)

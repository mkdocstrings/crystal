from __future__ import annotations

import contextlib
import xml.etree.ElementTree as etree
from typing import TYPE_CHECKING

import jinja2
import markdown_callouts
from markdown.treeprocessors import Treeprocessor
from markupsafe import Markup
from mkdocstrings import BaseHandler, CollectionError, HandlerOptions

from . import crystal_html

if TYPE_CHECKING:
    from .items import DocItem, DocPath


class CrystalRenderer(BaseHandler):
    fallback_theme = "material"

    @property
    def collector(self):
        return self

    def render(self, data: DocItem, options: HandlerOptions, *, locale: str | None = None) -> str:
        template = self.env.get_template(data._TEMPLATE)

        with self._monkeypatch_highlight_function(default_lang="crystal"):
            return template.render(
                config=options,
                obj=data,
                heading_level=options["heading_level"],
                root=True,
            )

    def get_aliases(self, identifier: str) -> tuple[str, ...]:
        try:
            data = self.collector.root.lookup(identifier)
            return (data.abs_id,)
        except CollectionError:
            return (identifier,)

    def update_env(self, config: dict) -> None:
        self._pymdownx_hl = None
        for ext in self.md.registeredExtensions:
            with contextlib.suppress(AttributeError):
                self._pymdownx_hl = ext.get_pymdownx_highlighter()  # type: ignore[attr-defined]

        # Disallow raw HTML.
        self.md.preprocessors.deregister("html_block")
        self.md.inlinePatterns.deregister("html")

        self.md.treeprocessors.register(
            _RefInsertingTreeprocessor(self.md), "mkdocstrings_crystal_xref", 12
        )
        markdown_callouts.CalloutsExtension().extendMarkdown(self.md)

        self.env.trim_blocks = True
        self.env.lstrip_blocks = True
        self.env.keep_trailing_newline = False
        self.env.undefined = jinja2.StrictUndefined

        self.env.filters["code_highlight"] = self.do_code_highlight
        self.env.filters["convert_markdown_ctx"] = self.do_convert_markdown_ctx
        self.env.filters["reference"] = self.do_reference

    def do_code_highlight(self, code, *, title: str = "", **kwargs) -> str:
        text = str(code)
        stext = text.lstrip()
        indent = text[: len(text) - len(stext)]
        html = self.env.filters["highlight"](stext, **kwargs)
        # HACK: Replace the end of the first tag with injected content.
        tag_end = Markup(">")
        if indent:
            html = html.replace(tag_end, tag_end + indent, 1)
        if isinstance(code, crystal_html.TextWithLinks):
            html = crystal_html.linkify_highlighted_html(html, code.tokens, self.do_reference)
        if title:
            prefix = Markup('<span class="doc-title">{}</span>').format(title)
            html = html.replace(tag_end, tag_end + prefix, 1)
        return html

    def do_reference(self, path: str | DocPath, text: str | None = None) -> str:
        if text is None:
            text = str(path)
        if "(" in str(path):
            return text
        try:
            ref_obj = self.collector.root.lookup(path)
        except CollectionError:
            return text
        else:
            return Markup('<span data-autorefs-optional="{}">{}</span>').format(
                ref_obj.abs_id, text
            )

    def do_convert_markdown_ctx(
        self, text: str, context: DocItem, heading_level: int, html_id: str
    ):
        p: _RefInsertingTreeprocessor = self.md.treeprocessors["mkdocstrings_crystal_xref"]  # type: ignore[assignment]
        p.context = context
        return super().do_convert_markdown(text, heading_level=heading_level, html_id=html_id)

    def _monkeypatch_highlight_function(self, default_lang: str):
        """Changes 'pymdownx.highlight' extension to use this lang by default."""
        # Yes, there really isn't a better way. I'd be glad to be proven wrong.
        if self._pymdownx_hl:
            old = self._pymdownx_hl.highlight

            def new(self, src="", language="", *args, **kwargs):
                return old(self, src, language or default_lang, *args, **kwargs)

            return _monkeypatch(self._pymdownx_hl, "highlight", new)
        return contextlib.nullcontext()


@contextlib.contextmanager
def _monkeypatch(obj, attr, func):
    old = getattr(obj, attr)
    setattr(obj, attr, func)
    try:
        yield
    finally:
        setattr(obj, attr, old)


class _RefInsertingTreeprocessor(Treeprocessor):
    context: DocItem | None

    def __init__(self, md):
        super().__init__(md)
        self.context = None

    def run(self, root: etree.Element):
        for i, el in enumerate(root):
            if el.tag != "code":
                self.run(el)
                continue

            assert self.context, "Bug: `CrystalRenderer` should have set the `context` member"
            try:
                ref_obj = self.context.lookup("".join(el.itertext()))
            except CollectionError:
                continue

            # Replace the `code` with a new `span` (need to propagate the tail too).
            root[i] = span = etree.Element("span")
            span.tail = el.tail
            el.tail = None
            # Put the `code` into the `span`, with a special attribute for mkdocstrings to pick up.
            span.append(el)
            span.set("data-autorefs-optional", ref_obj.abs_id)

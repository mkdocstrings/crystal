import contextlib
import xml.etree.ElementTree as etree
from typing import Optional, TypeVar, Union

import jinja2
from markdown import Markdown  # type: ignore
from markdown.extensions import Extension, fenced_code  # type: ignore
from markdown.treeprocessors import Treeprocessor
from markupsafe import Markup

from mkdocstrings.handlers import base

from . import crystal_html
from .items import DocItem, DocPath

T = TypeVar("T")


class CrystalRenderer(base.BaseRenderer):
    fallback_theme = "material"

    def render(self, data: DocItem, config: dict) -> str:
        subconfig = {
            "show_source_links": True,
            "heading_level": 2,
            **config,
        }
        template = self.env.get_template(data._TEMPLATE)

        with self._monkeypatch_highlight_function(default_lang="crystal"):
            return template.render(
                config=subconfig,
                obj=data,
                heading_level=subconfig["heading_level"],
                root=True,
            )

    def get_anchor(self, data: DocItem) -> str:
        return data.abs_id

    def update_env(self, md: Markdown, config: dict) -> None:
        super().update_env(md, config)
        self._md = md

        self._pymdownx_hl = None
        for ext in md.registeredExtensions:
            try:
                self._pymdownx_hl = ext.get_pymdownx_highlighter()
            except AttributeError:
                pass

        # Disallow raw HTML.
        del md.preprocessors["html_block"]
        del md.inlinePatterns["html"]

        md.treeprocessors.register(_RefInsertingTreeprocessor(md), "mkdocstrings_crystal_xref", 12)

        self.env.trim_blocks = True
        self.env.lstrip_blocks = True
        self.env.keep_trailing_newline = False
        self.env.undefined = jinja2.StrictUndefined

        self.env.filters["code_highlight"] = self.do_code_highlight
        self.env.filters["convert_markdown"] = self.do_convert_markdown
        self.env.filters["reference"] = self.do_reference

    def do_code_highlight(self, code, **kwargs) -> str:
        text = str(code)
        stext = text.lstrip()
        indent = text[: len(text) - len(stext)]
        html = indent + self.env.filters["highlight"](stext, **kwargs)
        if isinstance(code, crystal_html.TextWithLinks):
            html = crystal_html.linkify_highlighted_html(html, code.tokens, self.do_reference)
        return html

    def do_reference(self, path: Union[str, DocPath], text: Optional[str] = None) -> str:
        if text is None:
            text = str(path)
        if "(" in str(path):
            return text
        try:
            ref_obj = self.collector.root.lookup(path)
        except base.CollectionError:
            return text
        else:
            html = '<span data-mkdocstrings-identifier="{}">{}</span>'
            return Markup(html).format(ref_obj.abs_id, text)

    def do_convert_markdown(self, text: str, context: DocItem, heading_level: int, html_id: str):
        self._md.treeprocessors["mkdocstrings_crystal_xref"].context = context
        return super().do_convert_markdown(text, heading_level=heading_level, html_id=html_id)

    def _monkeypatch_highlight_function(self, default_lang: str):
        """Changes 'pymdownx.highlight' extension to use this lang by default."""
        # Yes, there really isn't a better way. I'd be glad to be proven wrong.
        if self._pymdownx_hl:
            old = self._pymdownx_hl.highlight
            new = lambda self, src="", language="", *args, **kwargs: old(
                self, src, language or default_lang, *args, **kwargs
            )
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
    context: Optional[DocItem]

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
            except base.CollectionError:
                continue

            # Replace the `code` with a new `span` (need to propagate the tail too).
            root[i] = span = etree.Element("span")
            span.tail = el.tail
            el.tail = None
            # Put the `code` into the `span`, with a special attribute for mkdocstrings to pick up.
            span.append(el)
            span.set("data-mkdocstrings-identifier", ref_obj.abs_id)

import collections
import contextlib
import xml.etree.ElementTree as etree
from typing import Optional, TypeVar, Union

import jinja2
from markdown import Markdown  # type: ignore
from markdown.extensions import Extension, fenced_code  # type: ignore
from markdown.treeprocessors import Treeprocessor
from markupsafe import Markup

from mkdocstrings.handlers import base

from .collector import CrystalCollector
from .items import DocItem, DocPath

T = TypeVar("T")


class CrystalRenderer(base.BaseRenderer):
    fallback_theme = "material"

    default_config: dict = {
        "show_source_links": True,
        "heading_level": 2,
    }

    def render(self, data: DocItem, config: dict) -> str:
        subconfig = collections.ChainMap(config, self.default_config)
        template = self.env.get_template(data._TEMPLATE)

        with self._monkeypatch_highlight_functions(default_lang="crystal"):
            return template.render(
                config=subconfig,
                obj=data,
                heading_level=subconfig["heading_level"],
                root=True,
            )

    def update_env(self, md: Markdown, config: dict) -> None:
        md = Markdown(extensions=config["mdx"], extension_configs=config["mdx_configs"])
        self._md = md

        self._pymdownx_hl = None
        for ext in md.registeredExtensions:
            if hasattr(ext, "get_pymdownx_highlighter"):
                self._pymdownx_hl = ext

        # Disallow raw HTML.
        del md.preprocessors["html_block"]
        del md.inlinePatterns["html"]

        base.ShiftHeadingsExtension().extendMarkdown(md)
        base.PrefixIdsExtension().extendMarkdown(md)
        XrefExtension(self.collector).extendMarkdown(md)

        self.env.trim_blocks = True
        self.env.lstrip_blocks = True
        self.env.keep_trailing_newline = False
        self.env.undefined = jinja2.StrictUndefined

        self.env.filters["convert_markdown"] = self.do_convert_markdown
        self.env.filters["reference"] = self.do_reference

    def do_reference(self, path: Union[str, DocPath]) -> str:
        if "(" in str(path):
            return str(path)
        try:
            ref_obj = self.collector.root.lookup(path)
        except base.CollectionError:
            return str(path)
        else:
            html = '<span data-mkdocstrings-identifier="{0}">{0}</span>'
            return Markup(html).format(ref_obj.abs_id)

    def do_convert_markdown(self, text: str, context: DocItem, heading_level: int, html_id: str):
        self._md.treeprocessors["mkdocstrings_crystal_xref"].context = context
        return base.do_convert_markdown(
            self._md, text, heading_level=heading_level, html_id=html_id
        )

    def _monkeypatch_highlight_functions(self, default_lang: str):
        """Changes 'codehilite' and 'pymdownx.highlight' extensions to use this lang by default."""
        # Yes, there really isn't a better way. I'd be glad to be proven wrong.
        if self._pymdownx_hl:
            old = self._pymdownx_hl.get_pymdownx_highlighter()
            members = {
                "highlight": lambda self, src="", language="", *args, **kwargs: old.highlight(
                    self, src, language or default_lang, *args, **kwargs
                )
            }
            subclass = type("Highlighter", (old,), members)
            return _monkeypatch(self._pymdownx_hl, "get_pymdownx_highlighter", lambda: subclass)
        else:
            old = fenced_code.CodeHilite
            new = lambda src, *args, lang=None, **kwargs: old(
                src, *args, lang=lang or default_lang, **kwargs
            )
            return _monkeypatch(fenced_code, "CodeHilite", new)


@contextlib.contextmanager
def _monkeypatch(obj, attr, func):
    old = getattr(obj, attr)
    setattr(obj, attr, func)
    try:
        yield
    finally:
        setattr(obj, attr, old)


class XrefExtension(Extension):
    def __init__(self, collector: CrystalCollector, **kwargs) -> None:
        super().__init__(**kwargs)
        self.collector = collector

    def extendMarkdown(self, md: Markdown) -> None:
        md.treeprocessors.register(_RefInsertingTreeprocessor(md), "mkdocstrings_crystal_xref", 12)


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

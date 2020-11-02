import collections
import xml.etree.ElementTree as etree
from typing import TypeVar

from markdown import Markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from markupsafe import Markup
from mkdocstrings.handlers.base import BaseRenderer, CollectionError

from .collector import CrystalCollector, DocObject

T = TypeVar("T")


class CrystalRenderer(BaseRenderer):
    fallback_theme = "material"

    default_config: dict = {
        "show_source": True,
        "heading_level": 2,
    }

    def render(self, data: DocObject, config: dict) -> str:
        final_config = collections.ChainMap(config, self.default_config)

        template = self.env.get_template(f"{data.JSON_KEY.rstrip('s')}.html")

        heading_level = final_config["heading_level"]

        return template.render(
            config=final_config,
            obj=data,
            heading_level=heading_level,
            root=True,
            toc_dedup=self._toc_dedup,
        )

    def update_env(self, md: Markdown, config: dict) -> None:
        if md != getattr(self, "_prev_md", None):
            self._prev_md = md

            extensions = list(config["mdx"])
            extensions.append(_EscapeHtmlExtension())
            extensions.append(XrefExtension(self.collector))
            self._md = Markdown(extensions=extensions, extension_configs=config["mdx_configs"])

            self._toc_dedup = _Deduplicator()

        super().update_env(self._md, config)
        self.env.trim_blocks = True
        self.env.lstrip_blocks = True
        self.env.keep_trailing_newline = False

        self.env.filters["convert_markdown"] = self._convert_markdown

    def _convert_markdown(self, text: str, context: DocObject):
        self._md.treeprocessors["mkdocstrings_crystal_xref"].context = context
        return Markup(self._md.convert(text))


class _Deduplicator:
    def __call__(self, value):
        if value != getattr(self, "value", object()):
            self.value = value
            return value


class _EscapeHtmlExtension(Extension):
    def extendMarkdown(self, md: Markdown):
        del md.preprocessors["html_block"]
        del md.inlinePatterns["html"]


class XrefExtension(Extension):
    def __init__(self, collector: CrystalCollector, **kwargs) -> None:
        super().__init__(**kwargs)
        self.collector = collector

    def extendMarkdown(self, md: Markdown) -> None:
        md.registerExtension(self)
        md.treeprocessors.register(
            _RefInsertingTreeprocessor(md, self.collector), "mkdocstrings_crystal_xref", 12
        )


class _RefInsertingTreeprocessor(Treeprocessor):
    def __init__(self, md, collector: CrystalCollector):
        super().__init__(md)
        self.collector = collector

    def run(self, root: etree.Element):
        for i, el in enumerate(root):
            if el.tag != "code":
                self.run(el)
                continue

            try:
                ref_obj = self.collector.collect("".join(el.itertext()), {}, context=self.context)
            except CollectionError:
                continue

            # Replace the `code` with a new `span` (need to propagate the tail too).
            root[i] = span = etree.Element("span")
            span.tail = el.tail
            # Put the old `code` into the `span`, wrap it into special text for mkdocstrings.
            span.text = "["
            span.append(el)
            el.tail = "][" + ref_obj.abs_id + "]"

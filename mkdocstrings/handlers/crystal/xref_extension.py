import xml.etree.ElementTree as etree
from typing import TYPE_CHECKING

from markdown import Markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from mkdocstrings.handlers.base import CollectionError

if TYPE_CHECKING:
    from mkdocstrings.handlers.crystal import CrystalCollector


class RefInsertingTreeprocessor(Treeprocessor):
    def __init__(self, md, collector: "CrystalCollector"):
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


class XrefExtension(Extension):
    def __init__(self, collector: "CrystalCollector", **kwargs) -> None:
        super().__init__(**kwargs)
        self.collector = collector

    def extendMarkdown(self, md: Markdown) -> None:
        md.registerExtension(self)
        md.treeprocessors.register(
            RefInsertingTreeprocessor(md, self.collector), "mkdocstrings_crystal_xref", 12
        )

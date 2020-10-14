import abc
import collections
import enum
import json
import re
import subprocess
from typing import Any, Optional, Union

from jinja2.filters import do_mark_safe
from markdown import Markdown

from mkdocstrings.handlers.base import BaseCollector, BaseHandler, BaseRenderer, CollectionError
from mkdocstrings.loggers import get_logger

from .xref_extension import XrefExtension

log = get_logger(__name__)


class DocObject(collections.UserDict, metaclass=abc.ABCMeta):
    JSON_KEY: str
    parent: Optional["DocObject"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = None
        for key, sublist in self.items():
            if key in DOC_TYPES:
                for subobj in sublist.values():
                    subobj.parent = self

    @property
    def rel_id(self):
        return self["name"]

    @property
    def abs_id(self):
        return self["id"]

    def __repr__(self):
        return type(self).__name__ + super().__repr__()


class DocType(DocObject):
    JSON_KEY = "types"

    @property
    def abs_id(self):
        return self["full_name"]


class DocConstant(DocObject):
    JSON_KEY = "constants"

    @property
    def abs_id(self):
        return (self.parent.abs_id + "::" if self.parent else "") + self.rel_id


class DocMethod(DocObject, metaclass=abc.ABCMeta):
    METHOD_SEP: str = ""
    METHOD_ID_SEP: str

    @property
    def rel_id(self):
        args = [arg["external_name"] for arg in self["args"]]
        if self.get("splat_index") is not None:
            args[self["splat_index"]] = "*" + args[self["splat_index"]]
        if self.get("double_splat"):
            args.append("**" + self["double_splat"]["external_name"])

        return self["name"] + "(" + ",".join(args) + ")"

    @property
    def abs_id(self):
        return (self.parent.abs_id if self.parent else "") + self.METHOD_ID_SEP + self.rel_id

    @property
    def short_name(self):
        return self.METHOD_SEP + self["name"]


class DocInstanceMethod(DocMethod):
    JSON_KEY = "instance_methods"
    METHOD_SEP = METHOD_ID_SEP = "#"


class DocClassMethod(DocMethod):
    JSON_KEY = "class_methods"
    METHOD_SEP = METHOD_ID_SEP = "."


class DocMacro(DocMethod):
    JSON_KEY = "macros"
    METHOD_ID_SEP = ":"


class DocConstructor(DocClassMethod):
    JSON_KEY = "constructors"


DOC_TYPES = {
    t.JSON_KEY: t
    for t in [DocType, DocInstanceMethod, DocClassMethod, DocMacro, DocConstructor, DocConstant]
}


class CrystalRenderer(BaseRenderer):
    fallback_theme = "material"

    default_config: dict = {
        "show_source": True,
        "heading_level": 2,
    }

    def render(self, data: DocObject, config: dict) -> str:
        final_config = dict(self.default_config)
        final_config.update(config)

        template = self.env.get_template(f"{data.JSON_KEY.rstrip('s')}.html")

        heading_level = final_config.pop("heading_level")

        return template.render(
            config=final_config, obj=data, heading_level=heading_level, root=True
        )

    def update_env(self, md: Markdown, config: dict) -> None:
        extensions = list(config["mdx"])
        extensions.append(XrefExtension(self.collector))
        self.md = Markdown(extensions=extensions, extension_configs=config["mdx_configs"])

        super().update_env(self.md, config)
        self.env.trim_blocks = True
        self.env.lstrip_blocks = True
        self.env.keep_trailing_newline = False

        self.env.filters["convert_markdown"] = self._convert_markdown
        self.env.globals["deduplicator"] = _Deduplicator

    def _convert_markdown(self, text: str, context: DocObject):
        self.md.treeprocessors["mkdocstrings_crystal_xref"].context = context
        return do_mark_safe(self.md.convert(text))


class _Deduplicator:
    def __call__(self, value):
        if value != getattr(self, "value", object()):
            self.value = value
            return value


def _object_hook(obj: dict) -> dict:
    for key, sublist in obj.items():
        if key in DOC_TYPES:
            obj[key] = newsublist = {}
            for subobj in sublist:
                newsubobj = DOC_TYPES[key](subobj)
                newsublist[newsubobj.rel_id] = newsubobj
    return obj


class CrystalCollector(BaseCollector):
    def __init__(self) -> None:
        outp = subprocess.check_output(
            [
                "crystal",
                "docs",
                "--format=json",
                "--project-name=",
                "--project-version=",
                "--source-refname=master",
            ]
        )
        self.data = json.loads(outp, object_hook=_object_hook)["program"]

    _LOOKUP_ORDER = {
        "": [DocType, DocConstant, DocInstanceMethod, DocClassMethod, DocConstructor, DocMacro],
        "::": [DocType, DocConstant],
        "#": [DocInstanceMethod, DocClassMethod, DocConstructor, DocMacro],
        ".": [DocClassMethod, DocConstructor, DocInstanceMethod, DocMacro],
        ":": [DocMacro],
    }

    def collect(
        self, identifier: str, config: dict, *, context: Optional[DocObject] = None
    ) -> DocObject:
        if identifier.startswith("::") or context is None:
            context = self.data
        obj = context

        path = re.split(r"(::|#|\.|:|^)", identifier)
        for sep, name in zip(path[1::2], path[2::2]):
            try:
                order = self._LOOKUP_ORDER[sep]
            except KeyError:
                raise CollectionError(f"{identifier!r} - unknown separator {sep!r}") from None
            mapp = collections.ChainMap(*(obj[t.JSON_KEY] for t in order if t.JSON_KEY in obj))
            try:
                obj = mapp[name]
            except KeyError:
                if context is not self.data:
                    return self.collect(identifier, config, context=context.parent)
                raise CollectionError(f"{identifier!r} - can't find {name!r}") from None

        return obj


class CrystalHandler(BaseHandler):
    pass


def get_handler(
    theme: str, custom_templates: Optional[str] = None, **config: Any
) -> CrystalHandler:
    collector = CrystalCollector()
    renderer = CrystalRenderer("crystal", theme, custom_templates)
    renderer.collector = collector
    return CrystalHandler(collector, renderer)

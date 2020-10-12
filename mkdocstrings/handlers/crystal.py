import abc
import collections
import enum
import json
import re
import subprocess
from typing import Any, Optional, Union

from markdown import Markdown

from mkdocstrings.handlers.base import BaseCollector, BaseHandler, BaseRenderer, CollectionError
from mkdocstrings.loggers import get_logger

log = get_logger(__name__)


class DocObject(collections.UserDict, metaclass=abc.ABCMeta):
    JSON_KEY: str
    parent: Optional[str]

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
    METHOD_SEP: str

    @property
    def rel_id(self):
        args = [arg["external_name"] for arg in self["args"]]
        if self.get("splat_index") is not None:
            args[self["splat_index"]] = "*" + args[self["splat_index"]]
        if self.get("double_splat"):
            args.append("**" + self["double_splat"]["external_name"])

        return self.METHOD_SEP + self["name"] + "(" + ",".join(args) + ")"

    @property
    def abs_id(self):
        return (self.parent.abs_id if self.parent else "") + self.rel_id


class DocInstanceMethod(DocMethod):
    JSON_KEY = "instance_methods"
    METHOD_SEP = "#"


class DocClassMethod(DocMethod):
    JSON_KEY = "class_methods"
    METHOD_SEP = "."


class DocMacro(DocMethod):
    JSON_KEY = "macros"
    METHOD_SEP = ":"


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
        super().update_env(md, config)
        self.env.trim_blocks = True
        self.env.lstrip_blocks = True
        self.env.keep_trailing_newline = False


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
        self.json = json.loads(outp, object_hook=_object_hook)

    def collect(self, identifier: str, config: dict) -> DocObject:
        if not identifier.startswith("::"):
            identifier = "::" + identifier

        obj = self.json["program"]

        path = re.split(r"(\W+)", identifier)
        for sep, name in zip(path[1::2], path[2::2]):
            try:
                if sep == "::":
                    mapp = collections.ChainMap(obj[DocType.JSON_KEY], obj[DocConstant.JSON_KEY])
                    obj = mapp[name]
                else:
                    if sep == ".":
                        order = [DocClassMethod, DocConstructor, DocInstanceMethod, DocMacro]
                    elif sep == "#":
                        order = [DocInstanceMethod, DocClassMethod, DocConstructor, DocMacro]
                    elif sep == ":":
                        order = [DocMacro]
                    else:
                        raise CollectionError(f"{identifier!r} - unknown separator {sep!r}")
                    mapp = collections.ChainMap(*(obj[t.JSON_KEY] for t in order))
                    obj = mapp[sep + name]
            except KeyError:
                raise CollectionError(f"{identifier!r} - can't find {name!r}")

        return obj


class CrystalHandler(BaseHandler):
    pass


def get_handler(
    theme: str, custom_templates: Optional[str] = None, **config: Any
) -> CrystalHandler:
    return CrystalHandler(
        collector=CrystalCollector(), renderer=CrystalRenderer("crystal", theme, custom_templates),
    )

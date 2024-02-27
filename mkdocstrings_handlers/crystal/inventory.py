from __future__ import annotations

import itertools
import json
import posixpath
from typing import IO, Iterator

from .items import DocModule


def read(file: IO) -> DocModule:
    data = json.load(file)
    data["program"]["full_name"] = ""
    return DocModule(data["program"], None, None)


def list_objects(obj) -> Iterator[tuple[str, str]]:
    path = obj.data["path"]

    if obj.full_name:
        yield obj.abs_id, path

    for const in obj.constants:
        yield const.abs_id, path + "#" + const.name

    for meth in itertools.chain(
        obj.constructors, obj.class_methods, obj.instance_methods, obj.macros
    ):
        yield meth.abs_id, path + "#" + meth.data["html_id"]

    for typ in obj.types:
        yield from list_objects(typ)


def list_object_urls(
    in_file: IO, url: str = "", base_url: str | None = None, **kwargs
) -> Iterator[tuple[str, str]]:
    if base_url is None:
        if url.endswith("/index.json"):
            base_url = url[: -len("/index.json")]
        else:
            base_url = url

    for abs_id, path in list_objects(read(in_file)):
        yield abs_id, posixpath.join(base_url, path)

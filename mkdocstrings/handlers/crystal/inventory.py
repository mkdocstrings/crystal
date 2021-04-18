import itertools
import json
import posixpath

from .items import DocModule


def read(file) -> DocModule:
    data = json.load(file)
    data["program"]["full_name"] = ""
    return DocModule(data["program"], None, None)


def list_objects(obj):
    path = obj.data["path"]

    if obj.full_name:
        yield obj.abs_id, path

    for const in obj.constants:
        yield const.abs_id, path + "#" + const.name

    for meth in itertools.chain(
        obj.constructors, obj.class_methods, obj.instance_methods, obj.macros
    ):
        for abs_id in meth.abs_id, meth.abs_id.split("(", 1)[0]:
            yield abs_id, path + "#" + meth.data["html_id"]

    for typ in obj.types:
        yield from list_objects(typ)


def list_object_urls(file, url="", **kwargs):
    if url.endswith("/index.json"):
        url = url[: -len("/index.json")]

    for abs_id, path in list_objects(read(file)):
        yield abs_id, posixpath.join(url, path)

import collections
import json
import re
import subprocess
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence, TypeVar, Union

from cached_property import cached_property
from mkdocstrings.handlers.base import BaseCollector, CollectionError

from .items import DocConstant, DocItem, DocMapping, DocMethod, DocType

D = TypeVar("D", bound=DocItem)


class CrystalCollector(BaseCollector):
    default_config: dict = {
        "nested_types": False,
        "file_filters": True,
    }

    def __init__(self, crystal_docs_flags: Sequence[str] = ()):
        self._proc = subprocess.Popen(
            [
                "crystal",
                "docs",
                "--format=json",
                "--project-name=",
                "--project-version=",
                "--source-refname=master",
                *crystal_docs_flags,
            ],
            stdout=subprocess.PIPE,
        )

    @cached_property
    def root(self) -> DocType:
        """The top-level namespace, represented as a fake module."""
        with self._proc:
            return DocType(json.load(self._proc.stdout)["program"], None, None)

    def collect(
        self, identifier: str, config: Mapping[str, Any], *, context: Optional[DocItem] = None
    ) -> DocItem:
        config = collections.ChainMap(config, self.default_config)

        return DocView((context or self.root).lookup(identifier), config)


class DocView(DocItem):
    def __init__(self, item: DocItem, config: Mapping[str, Any]):
        self._item = item
        self._config = config

    def __getattribute__(self, name: str):
        item = super().__getattribute__("_item")
        config = super().__getattribute__("_config")

        val = getattr(item, name)
        if isinstance(val, DocMapping) and val:
            if name == "types" and not config["nested_types"]:
                return DocMapping(())
            return type(self)._filter(config["file_filters"], val, type(self)._get_locations)
        return val

    @classmethod
    def _get_locations(cls, obj: DocItem) -> Sequence[str]:
        if isinstance(obj, DocConstant):
            obj = obj.parent
            if not obj:
                return ()
        if isinstance(obj, DocType):
            return [loc.url.rsplit("#", 1)[0] for loc in obj.locations]
        elif isinstance(obj, DocMethod):
            if not obj.location:
                return ()
            return (obj.location.url.rsplit("#", 1)[0],)
        else:
            raise TypeError(obj)

    @classmethod
    def _filter(
        cls,
        filters: Union[bool, Sequence[str]],
        mapp: DocMapping[D],
        getter: Callable[[D], Sequence[str]],
    ) -> DocMapping[D]:
        if filters is False:
            return DocMapping(())
        if filters is True:
            return mapp
        try:
            re.compile(filters[0])
        except (TypeError, IndexError):
            raise CollectionError(
                f"Expected a non-empty list of strings as filters, not {filters!r}"
            )

        return DocMapping([item for item in mapp if _apply_filter(filters, getter(item))])


def _apply_filter(
    filters: Iterable[str],
    tags: Sequence[str],
) -> bool:
    match = False
    for filt in filters:
        filter_kind = True
        if filt.startswith("!"):
            filter_kind = False
            filt = filt[1:]
        if any(re.search(filt, s) for s in tags):
            match = filter_kind
    return match

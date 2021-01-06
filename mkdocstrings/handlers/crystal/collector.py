import collections
import json
import logging
import re
import shlex
import subprocess
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence, TypeVar, Union

import mkdocs.utils
from cached_property import cached_property
from mkdocstrings.handlers.base import BaseCollector, CollectionError

from .items import DocConstant, DocItem, DocMapping, DocMethod, DocModule, DocType

log = logging.getLogger(f"mkdocs.plugins.{__name__}")
log.addFilter(mkdocs.utils.warning_filter)

D = TypeVar("D", bound=DocItem)


class CrystalCollector(BaseCollector):
    default_config: dict = {
        "nested_types": False,
        "file_filters": True,
    }

    def __init__(self, crystal_docs_flags: Sequence[str] = ()):
        """Create a "collector", reading docs from `crystal doc` in the current directory.

        When using mkdocstrings-crystal within MkDocs, a plugin can access the instance as `config['plugins']['mkdocstrings'].get_handler('crystal').collector`.
        """
        command = [
            "crystal",
            "docs",
            "--format=json",
            "--project-name=",
            "--project-version=",
            "--source-refname=master",
            *crystal_docs_flags,
        ]
        log.debug("Running `%s`", " ".join(shlex.quote(arg) for arg in command))

        self._proc = subprocess.Popen(command, stdout=subprocess.PIPE)
        self._collected = collections.Counter()

    @cached_property
    def root(self) -> DocModule:
        """The top-level namespace, represented as a fake module."""
        with self._proc:
            return DocModule(json.load(self._proc.stdout)["program"], None, None)

    def collect(self, identifier: str, config: Mapping[str, Any]) -> "DocView":
        """[Find][mkdocstrings.handlers.crystal.items.DocItem.lookup] an item by its identifier.

        Raises:
            CollectionError: When an item by that identifier couldn't be found.
        """
        config = collections.ChainMap(config, self.default_config)

        item = self.root.lookup(identifier)
        view = DocView(item, config)
        if isinstance(item, DocType):
            self._collected.update((item,))
            self._collected.update(view.walk_types())
        else:
            self._collected.setdefault(item.parent, 0)

        return view

    def teardown(self):
        if log.isEnabledFor(logging.DEBUG):
            mul_collected = ", ".join(
                typ.abs_id for typ in self.root.walk_types() if self._collected[typ] > 1
            )
            if mul_collected:
                log.debug(
                    f"These types were put into the documentation more than once: {mul_collected}"
                )
            not_collected = ", ".join(
                typ.abs_id for typ in self.root.walk_types() if typ not in self._collected
            )
            if not_collected:
                log.debug(f"These types were never put into the documentation: {not_collected}")


class DocView:
    def __init__(self, item: DocItem, config: Mapping[str, Any]):
        self.item = item
        self.config = config

    def __getattr__(self, name: str):
        val = getattr(self.item, name)
        if isinstance(val, DocMapping) and val:
            if name == "types" and not self.config["nested_types"]:
                return DocMapping(())
            return type(self)._filter(self.config["file_filters"], val, type(self)._get_locations)
        return val

    def walk_types(self) -> Iterator[DocType]:
        types = self.types  # type: DocMapping[DocType]
        for typ in types:
            yield typ
            yield from typ.walk_types()

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

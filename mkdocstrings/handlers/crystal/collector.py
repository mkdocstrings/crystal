import collections
import dataclasses
import functools
import logging
import os
import re
import shlex
import subprocess
from typing import Any, Callable, Iterable, Iterator, List, Mapping, Sequence, TypeVar, Union, cast

import mkdocs.exceptions
import mkdocs.utils
from cached_property import cached_property
from mkdocstrings.handlers.base import BaseCollector, CollectionError

from . import inventory
from .items import DocConstant, DocItem, DocLocation, DocMapping, DocMethod, DocModule, DocType

try:
    from mkdocs.exceptions import PluginError
except ImportError:
    PluginError = SystemExit

log = logging.getLogger(f"mkdocs.plugins.{__name__}")
log.addFilter(mkdocs.utils.warning_filter)

D = TypeVar("D", bound=DocItem)


class CrystalCollector(BaseCollector):
    def __init__(
        self, crystal_docs_flags: Sequence[str] = (), source_locations: Mapping[str, str] = {}
    ):
        """Create a "collector", reading docs from `crystal doc` in the current directory.

        Normally this should not be instantiated.

        When using mkdocstrings-crystal within MkDocs, a plugin can access the instance as `config['plugins']['mkdocstrings'].get_handler('crystal').collector`.

        See [Extras](extras.md).
        """
        command = [
            "crystal",
            "docs",
            "--format=json",
            "--project-name=",
            "--project-version=",
        ]
        if source_locations:
            command.append("--source-refname=master")
        command += (s.format_map(_crystal_info) for s in crystal_docs_flags)
        log.debug("Running `%s`", " ".join(shlex.quote(arg) for arg in command))

        self._proc = subprocess.Popen(command, stdout=subprocess.PIPE)

        # For unambiguous prefix match: add trailing slash, sort by longest path first.
        self._source_locations = sorted(
            (
                _SourceDestination(os.path.relpath(k) + os.sep, source_locations[k])
                for k in source_locations
            ),
            key=lambda d: -d.src_path.count("/"),
        )

    # pytype: disable=bad-return-type
    @cached_property
    def root(self) -> "DocRoot":
        """The top-level namespace, represented as a fake module."""
        try:
            with self._proc:
                root = inventory.read(self._proc.stdout)
            root.__class__ = DocRoot
            root.source_locations = self._source_locations
            return root
        finally:
            if self._proc.returncode:
                cmd = " ".join(shlex.quote(arg) for arg in self._proc.args)
                raise PluginError(f"Command `{cmd}` exited with status {self._proc.returncode}")

    # pytype: enable=bad-return-type

    def collect(self, identifier: str, config: Mapping[str, Any]) -> "DocView":
        """[Find][mkdocstrings.handlers.crystal.items.DocItem.lookup] an item by its identifier.

        Raises:
            CollectionError: When an item by that identifier couldn't be found.
        """
        config = {
            "nested_types": False,
            "file_filters": True,
            **config,
        }

        item = self.root
        if identifier != "::":
            item = item.lookup(identifier)
        return DocView(item, config)


@dataclasses.dataclass
class _SourceDestination:
    src_path: str
    dest_url: str

    def substitute(self, location: DocLocation) -> str:
        data = {"file": location.filename[len(self.src_path) :], "line": location.line}
        try:
            return self.dest_url.format_map(collections.ChainMap(data, _DictAccess(self), _crystal_info))  # type: ignore
        except KeyError as e:
            raise PluginError(
                f"The source_locations template {self.dest_url!r} did not resolve correctly: {e}"
            )

    @property
    def shard_version(self) -> str:
        return self._shard_version(os.path.dirname(self.src_path))

    @classmethod
    @functools.lru_cache(maxsize=None)
    def _shard_version(cls, path: str) -> str:
        file_path = _find_above(path, "shard.yml")
        with open(file_path, "rb") as f:
            m = re.search(rb"^version: *([\S+]+)", f.read(), flags=re.MULTILINE)
        if not m:
            raise PluginError(f"`version:` not found in {file_path!r}")
        return m[1].decode()


def _find_above(path: str, filename: str) -> str:
    orig_path = path
    while path:
        file_path = os.path.join(path, filename)
        if os.path.isfile(file_path):
            return file_path
        path = os.path.dirname(path)
    raise PluginError(f"{filename!r} not found anywhere above {os.path.abspath(orig_path)!r}")


class _CrystalInfo:
    @cached_property
    def crystal_version(self) -> str:
        return subprocess.check_output(
            ["crystal", "env", "CRYSTAL_VERSION"], encoding="ascii"
        ).rstrip()

    @cached_property
    def crystal_src(self) -> str:
        out = subprocess.check_output(["crystal", "env", "CRYSTAL_PATH"], text=True).rstrip()
        for path in out.split(os.pathsep):
            if os.path.isfile(os.path.join(path, "prelude.cr")):
                return os.path.relpath(path)
        raise PluginError(f"Crystal sources not found anywhere in CRYSTAL_PATH={out!r}")


class _DictAccess:
    def __init__(self, obj):
        self.obj = obj

    def __getitem__(self, key):
        try:
            return getattr(self.obj, key)
        except AttributeError as e:
            raise KeyError(f"Missing key: {e}")


_crystal_info = _DictAccess(_CrystalInfo())


class DocRoot(DocModule):
    source_locations: List[_SourceDestination]

    def update_url(self, location: DocLocation) -> DocLocation:
        for dest in self.source_locations:
            if (location.filename or "").startswith(dest.src_path):
                location.url = dest.substitute(location)
                break
        return location


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
        types = cast(DocMapping[DocType], self.types)
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

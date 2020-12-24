from __future__ import annotations

import abc
import collections
import dataclasses
import re
from typing import Any, Generic, Iterator, Mapping, Optional, Sequence, TypeVar, Union

from cached_property import cached_property
from mkdocstrings.handlers.base import CollectionError


class DocItem(metaclass=abc.ABCMeta):
    """A representation of a documentable item from Crystal language.

    Acts as a dictionary that (additionally) always has these keys:

    * `doc`: `str`
    """

    _TEMPLATE: str
    parent: Optional["DocItem"] = None
    """The item that is the parent namespace for this item."""
    root: "DocType" = None

    def __init__(self, data: Mapping[str, Any], parent: Optional[DocItem], root: Optional[DocType]):
        self.data = data
        self.parent = parent
        self.root = root or self

    @property
    def name(self) -> str:
        """The name of this item, e.g. `Foo` or `baz`."""
        return self.data["name"]

    @property
    def rel_id(self) -> str:
        """The relative identifier of this item, e.g. `Foo` or `baz(x,y)`."""
        return self.data["name"]

    @property
    def abs_id(self) -> str:
        """The absolute identifier of this item, sometimes known as "path", e.g. `Foo::Bar` or `Foo::Bar#baz(x,y)`.

        This is also the canonical identifier that will be used as its HTML id."""
        return self.data["id"]

    @property
    def doc(self) -> str:
        return self.data["doc"]

    @classmethod
    def _properties(cls):
        for attr in dir(cls):
            if attr.startswith("_") or attr in ("doc", "abs_id", "name", "kind"):
                continue
            if isinstance(getattr(cls, attr), (property, cached_property)):
                yield attr

    def __repr__(self) -> str:
        items = ", ".join(
            f"{attr}={getattr(self, attr)!r}" for attr in self._properties() if getattr(self, attr)
        )
        return f"{type(self).__name__}({items})"

    def __bool__(self):
        return True

    def lookup(self, identifier: Union[str, DocPath]) -> DocItem:
        """Find an item by its identifier, relative to this item or the root.

        Raises:
            CollectionError: When an item by that identifier couldn't be found.
        """
        if isinstance(identifier, DocPath):
            identifier = "::" + identifier.abs_id
        obj = self.root if identifier.startswith("::") else self
        ret_obj = obj
        path = re.split(r"(::|#|\.|:|^)", identifier)
        for sep, name in zip(path[1::2], path[2::2]):
            if isinstance(obj, DocType):
                try:
                    order = _LOOKUP_ORDER[sep]
                except KeyError:
                    raise CollectionError(f"{identifier!r} - unknown separator {sep!r}") from None
                mapp = collections.ChainMap(*(getattr(obj, a) for a in order))
                obj = mapp.get(name.replace(" ", "")) or mapp.get(name.split("(", 1)[0])
            else:
                obj = None
            if obj is None:
                if self.parent:
                    return self.parent.lookup(identifier)
                raise CollectionError(f"{identifier!r} - can't find {name!r}")
            ret_obj = obj
            if isinstance(obj, DocAlias):
                try:
                    obj = self.lookup(obj.aliased)
                except CollectionError:
                    pass
        return ret_obj


_LOOKUP_ORDER = {
    "": ["types", "constants", "instance_methods", "class_methods", "constructors", "macros"],
    "::": ["types", "constants"],
    "#": ["instance_methods", "class_methods", "constructors", "macros"],
    ".": ["class_methods", "constructors", "instance_methods", "macros"],
    ":": ["macros"],
}


D = TypeVar("D", bound=DocItem)


class DocType(DocItem):
    """A [DocItem][mkdocstrings.handlers.crystal.items.DocItem] representing a Crystal type."""

    _TEMPLATE = "type.html"

    def __new__(cls, data: Mapping[str, Any] = None, *args, **kwargs) -> DocType:
        if cls is DocType:
            cls = {
                "module": DocModule,
                "class": DocClass,
                "struct": DocStruct,
                "enum": DocEnum,
                "alias": DocAlias,
                "annotation": DocAnnotation,
            }[data["kind"]]
            return cls.__new__(cls, data, *args, **kwargs)
        return super().__new__(cls)

    @property
    def abs_id(self):
        # Drop the possible generic part.
        return self.full_name.split("(", 1)[0]

    @property
    def full_name(self) -> str:
        """The path of this item, e.g. `Foo::Bar(T)` or `baz`."""
        return self.data["full_name"]

    @property
    def kind(self) -> str:
        """module, class, struct, enum, alias, annotation"""
        return self.data["kind"]

    @property
    def is_abstract(self) -> bool:
        return self.data["abstract"]

    @cached_property
    def constants(self) -> DocMapping[DocConstant]:
        return DocMapping([DocConstant(x, self, self.root) for x in self.data["constants"]])

    @cached_property
    def instance_methods(self) -> DocMapping[DocInstanceMethod]:
        return DocMapping(
            [DocInstanceMethod(x, self, self.root) for x in self.data["instance_methods"]]
        )

    @cached_property
    def class_methods(self) -> DocMapping[DocClassMethod]:
        return DocMapping([DocClassMethod(x, self, self.root) for x in self.data["class_methods"]])

    @cached_property
    def constructors(self) -> DocMapping[DocConstructor]:
        return DocMapping([DocConstructor(x, self, self.root) for x in self.data["constructors"]])

    @cached_property
    def macros(self) -> DocMapping[DocMacro]:
        return DocMapping([DocMacro(x, self, self.root) for x in self.data["macros"]])

    @cached_property
    def types(self) -> DocMapping[DocType]:
        return DocMapping([DocType(x, self, self.root) for x in self.data["types"]])

    @cached_property
    def superclass(self) -> Optional[DocPath]:
        if self.data["superclass"] is not None:
            return DocPath(self.data["superclass"], self)

    @cached_property
    def ancestors(self) -> Sequence[DocPath]:
        return [DocPath(x, self) for x in self.data["ancestors"]]

    @cached_property
    def included_modules(self) -> Sequence[DocPath]:
        return [DocPath(x, self) for x in self.data["included_modules"]]

    @cached_property
    def extended_modules(self) -> Sequence[DocPath]:
        return [DocPath(x, self) for x in self.data["extended_modules"]]

    @cached_property
    def subclasses(self) -> Sequence[DocPath]:
        return [DocPath(x, self) for x in self.data["subclasses"]]

    @cached_property
    def including_types(self) -> Sequence[DocPath]:
        return [DocPath(x, self) for x in self.data["including_types"]]

    @cached_property
    def locations(self) -> Sequence[DocLocation]:
        return [
            DocLocation(loc["filename"], loc["line_number"], loc["url"])
            for loc in self.data["locations"]
        ]

    def walk_types(self) -> Iterator["DocType"]:
        """Iterate over all types under this type (excl. itself) in lexicographic order."""
        for typ in self.types:
            yield typ
            yield from typ.walk_types()


class DocModule(DocType):
    pass


class DocClass(DocType):
    pass


class DocStruct(DocType):
    pass


class DocEnum(DocType):
    pass


class DocModule(DocType):
    pass


class DocAlias(DocType):
    @property
    def aliased(self):
        assert self.data["aliased"]
        return self.data["aliased"]


class DocAnnotation(DocType):
    pass


class DocConstant(DocItem):
    """A [DocItem][mkdocstrings.handlers.crystal.items.DocItem] representing a Crystal constant definition."""

    @property
    def full_name(self):
        return (self.parent.full_name + "::" if self.parent else "") + self.name

    @property
    def abs_id(self):
        return (self.parent.abs_id + "::" if self.parent else "") + self.rel_id

    @property
    def kind(self) -> str:
        """constant"""
        return "constant"

    @property
    def value(self) -> str:
        return self.data["value"]


class DocMethod(DocItem, metaclass=abc.ABCMeta):
    """A [DocItem][mkdocstrings.handlers.crystal.items.DocItem] representing a Crystal method."""

    _TEMPLATE = "method.html"
    METHOD_SEP: str = ""
    METHOD_ID_SEP: str

    @property
    def rel_id(self):
        d = self.data["def"]

        args = [arg["external_name"] for arg in d["args"]]
        if d.get("splat_index") is not None:
            args[d["splat_index"]] = "*" + args[d["splat_index"]]
        if d.get("double_splat"):
            args.append("**" + d["double_splat"]["external_name"])
        if d.get("block_arg"):
            args.append("&")

        return self.name + "(" + ",".join(args) + ")"

    @property
    def abs_id(self):
        return (self.parent.abs_id if self.parent else "") + self.METHOD_ID_SEP + self.rel_id

    @property
    def short_name(self):
        """Similar to [rel_id][mkdocstrings.handlers.crystal.items.DocItem.rel_id], but also includes the separator first, e.g. `#bar(x,y)` or `.baz()`"""
        return self.METHOD_SEP + self.name

    @property
    @abc.abstractmethod
    def kind(self) -> str:
        """instance_method, class_method, macro"""

    @property
    def is_abstract(self):
        return self.data["abstract"]

    @property
    def args(self) -> Mapping[str, Any]:
        return self.data["args"]

    @property
    def args_string(self) -> str:
        return re.sub(r"<[\w/].*?>", "", self.data["args_string"])

    @cached_property
    def location(self) -> Optional[DocLocation]:
        m = re.fullmatch(r".+?/(?:blob|tree)/[^/]+/(.+)#L(\d+)", self.data.get("source_link") or "")
        if m:
            filename, line = m.groups()
            return DocLocation(filename, line, self.data.get("source_link"))


class DocInstanceMethod(DocMethod):
    """A [DocMethod][mkdocstrings.handlers.crystal.items.DocMethod] representing a Crystal instance method."""

    METHOD_SEP = METHOD_ID_SEP = "#"

    @property
    def kind(self):
        return "instance_method"


class DocClassMethod(DocMethod):
    """A [DocMethod][mkdocstrings.handlers.crystal.items.DocMethod] representing a Crystal class method."""

    METHOD_SEP = METHOD_ID_SEP = "."

    @property
    def kind(self):
        return "class_method"


class DocMacro(DocMethod):
    """A [DocMethod][mkdocstrings.handlers.crystal.items.DocMethod] representing a Crystal macro."""

    METHOD_ID_SEP = ":"

    @property
    def kind(self):
        return "macro"


class DocConstructor(DocClassMethod):
    """A [DocInstanceMethod][mkdocstrings.handlers.crystal.items.DocInstanceMethod] representing a Crystal macro."""

    _TEMPLATE = "constant.html"


class DocMapping(Generic[D]):
    items: Sequence = ()
    search: Mapping[str, Any] = {}

    def __init__(self, items: Sequence[D]):
        if items:
            self.items = items
            self.search = search = {}
            for item in self.items:
                search.setdefault(item.rel_id, item)
                search.setdefault(item.name, item)

    def __iter__(self) -> Iterator[D]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __bool__(self) -> bool:
        return bool(self.items)

    def __contains__(self, key: str) -> bool:
        return key in self.search

    def __getitem__(self, key: str) -> D:
        return self.search[key]

    def __add__(self, other: DocMapping) -> DocMapping:
        new = type(self).__new__(type(self))
        if self.items and other.items:
            new.items = [*self.items, *other.items]
        else:
            new.items = self.items or other.items
        new.search = collections.ChainMap(new.search, other.search)
        return new

    def __repr__(self):
        items = ", ".join(repr(item.rel_id) for item in self.items)
        return f"{type(self).__name__}{{{items}}}"


@dataclasses.dataclass
class DocLocation:
    filename: str
    line: int
    url: Optional[str]


class DocPath:
    def __init__(self, data: Mapping[str, Any], root: DocType):
        self.data = data
        self.root = root

    @property
    def full_name(self) -> str:
        """The path of this item, e.g. `Foo::Bar(T)` or `baz`."""
        return self.data["full_name"]

    @property
    def abs_id(self) -> str:
        return self.full_name.split("(", 1)[0]

    def lookup(self) -> DocItem:
        return self.root.lookup(self.abs_id)

    def __str__(self) -> str:
        return self.full_name

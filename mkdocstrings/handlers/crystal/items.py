from __future__ import annotations

import abc
import collections
import dataclasses
import re
from typing import Any, Generic, Iterator, Mapping, Optional, Sequence, TypeVar, Union

from cached_property import cached_property
from mkdocstrings.handlers.base import CollectionError

from . import crystal_html


class DocItem(metaclass=abc.ABCMeta):
    """A representation of a documentable item from Crystal language."""

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
        """The doc comment of this item."""
        return self.data["doc"]

    @classmethod
    def _properties(cls):
        for attr in dir(cls):
            if attr.startswith("_") or attr in ("doc", "abs_id", "name", "kind"):
                continue
            if isinstance(getattr(cls, attr), (property, cached_property)):
                yield attr

    @property
    @abc.abstractmethod
    def kind(self) -> str:
        """One of:

        * *module, class, struct, enum, alias, annotation,*
        * *instance_method, class_method, macro,*
        * *constant*
        """

    def __repr__(self) -> str:
        items = ", ".join(
            f"{attr}={getattr(self, attr)!r}" for attr in self._properties() if getattr(self, attr)
        )
        return f"{type(self).__name__}({items})"

    def lookup(self, identifier: Union[str, DocPath]) -> DocItem:
        """Find an item by its identifier, relative to this item or the root.

        Params:
            identifier: The item to search for.
        Returns:
            An object that's a subclass of DocItem.
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
                    obj = self.lookup(str(obj.aliased))
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
        """Based on Crystal's JSON, create an object of an appropriate subclass of DocType"""
        if cls is DocType:
            try:
                cls = {
                    "module": DocModule,
                    "class": DocClass,
                    "struct": DocStruct,
                    "enum": DocEnum,
                    "alias": DocAlias,
                    "annotation": DocAnnotation,
                }[data["kind"]]
            except KeyError:
                raise TypeError(
                    "DocType is abstract, and {kind!r} is not recognized".format_map(data)
                )
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
        return self.data["kind"]

    @property
    def is_abstract(self) -> bool:
        """Whether this type is abstract."""
        return self.data["abstract"]

    @cached_property
    def constants(self) -> DocMapping[DocConstant]:
        """The constants (or enum members) within this type."""
        return DocMapping([DocConstant(x, self, self.root) for x in self.data["constants"]])

    @cached_property
    def instance_methods(self) -> DocMapping[DocInstanceMethod]:
        """The instance methods within this type."""
        return DocMapping(
            [DocInstanceMethod(x, self, self.root) for x in self.data["instance_methods"]]
        )

    @cached_property
    def class_methods(self) -> DocMapping[DocClassMethod]:
        """The class methods within this type."""
        return DocMapping([DocClassMethod(x, self, self.root) for x in self.data["class_methods"]])

    @cached_property
    def constructors(self) -> DocMapping[DocConstructor]:
        """The constructors within this type."""
        return DocMapping([DocConstructor(x, self, self.root) for x in self.data["constructors"]])

    @cached_property
    def macros(self) -> DocMapping[DocMacro]:
        """The macros within this type."""
        return DocMapping([DocMacro(x, self, self.root) for x in self.data["macros"]])

    @cached_property
    def types(self) -> DocMapping[DocType]:
        """The types nested in this type as a namespace."""
        return DocMapping([DocType(x, self, self.root) for x in self.data["types"]])

    @cached_property
    def superclass(self) -> Optional[DocPath]:
        """The possible superclass of this type."""
        if self.data["superclass"] is not None:
            return DocPath(self.data["superclass"], self)

    @cached_property
    def ancestors(self) -> Sequence[DocPath]:
        """The modules and classes this type inherited."""
        return [DocPath(x, self) for x in self.data["ancestors"]]

    @cached_property
    def included_modules(self) -> Sequence[DocPath]:
        """The modules that this type included."""
        return [DocPath(x, self) for x in self.data["included_modules"]]

    @cached_property
    def extended_modules(self) -> Sequence[DocPath]:
        """The modules that this type extended."""
        return [DocPath(x, self) for x in self.data["extended_modules"]]

    @cached_property
    def subclasses(self) -> Sequence[DocPath]:
        """Known subclasses of this type."""
        return [DocPath(x, self) for x in self.data["subclasses"]]

    @cached_property
    def including_types(self) -> Sequence[DocPath]:
        """Known types that include this type."""
        return [DocPath(x, self) for x in self.data["including_types"]]

    @cached_property
    def locations(self) -> Sequence[DocLocation]:
        """The [code locations][mkdocstrings.handlers.crystal.items.DocLocation] over which the definitions of this type span."""
        return [
            self.root.update_url(DocLocation(loc["filename"], loc["line_number"], loc["url"]))
            for loc in self.data["locations"]
        ]

    def walk_types(self) -> Iterator[DocType]:
        """Recusively iterate over all types under this type (excl. itself) in lexicographic order."""
        for typ in self.types:
            yield typ
            yield from typ.walk_types()


class DocModule(DocType):
    """A [DocType][mkdocstrings.handlers.crystal.items.DocType] representing a Crystal module."""


class DocClass(DocType):
    """A [DocType][mkdocstrings.handlers.crystal.items.DocType] representing a Crystal class."""


class DocStruct(DocType):
    """A [DocType][mkdocstrings.handlers.crystal.items.DocType] representing a Crystal struct."""


class DocEnum(DocType):
    """A [DocType][mkdocstrings.handlers.crystal.items.DocType] representing a Crystal enum."""


class DocAlias(DocType):
    """A [DocType][mkdocstrings.handlers.crystal.items.DocType] representing a Crystal alias."""

    @cached_property
    def aliased(self) -> crystal_html.TextWithLinks:
        """[A rich string][mkdocstrings.handlers.crystal.crystal_html.TextWithLinks] containing the definition of what this is aliased to."""
        # https://github.com/crystal-lang/crystal/pull/10117
        try:
            return crystal_html.parse_crystal_html(self.data["aliased_html"])
        except KeyError:
            return crystal_html.TextWithLinks(self.data["aliased"], ())

    @property
    def constants(self):
        # Crystal duplicates constants into aliases, but that's undesirable.
        return DocMapping(())


class DocAnnotation(DocType):
    """A [DocType][mkdocstrings.handlers.crystal.items.DocType] representing a Crystal annotation."""


class DocConstant(DocItem):
    """A [DocItem][mkdocstrings.handlers.crystal.items.DocItem] representing a Crystal constant definition."""

    _TEMPLATE = "constant.html"

    @property
    def full_name(self):
        return (self.parent.full_name + "::" if self.parent else "") + self.name

    @property
    def abs_id(self):
        return (
            self.parent.abs_id + "::" if self.parent and self.parent.parent else ""
        ) + self.rel_id

    @property
    def kind(self) -> str:
        return "constant"

    @property
    def value(self) -> str:
        """The value of the constant (the code as a string)."""
        return self.data["value"]


class DocMethod(DocItem):
    """A [DocItem][mkdocstrings.handlers.crystal.items.DocItem] representing a Crystal method."""

    _TEMPLATE = "method.html"
    METHOD_SEP: str = ""
    METHOD_ID_SEP: str

    @property
    def rel_id(self):
        d = self.data["def"]

        args = [arg["external_name"] for arg in d["args"]]
        if d.get("splat_index") is not None:
            args[d["splat_index"]] = "*"
        if d.get("double_splat"):
            args.append("**")
        if d.get("block_arg") or d.get("yields"):
            args.append("&")

        return self.name + ("(" + ",".join(args) + ")" if args else "")

    @property
    def abs_id(self):
        return (
            self.parent.abs_id + self.METHOD_ID_SEP if self.parent and self.parent.parent else ""
        ) + self.rel_id

    @property
    def short_name(self):
        """Similar to [rel_id][mkdocstrings.handlers.crystal.items.DocItem.rel_id], but also includes the separator first, e.g. `#bar(x,y)` or `.baz()`"""
        return (self.METHOD_SEP if self.parent and self.parent.parent else "") + self.name

    @property
    def is_abstract(self) -> bool:
        """Whether this method is abstract."""
        return self.data["abstract"]

    @cached_property
    def args_string(self) -> crystal_html.TextWithLinks:
        """[A rich string][mkdocstrings.handlers.crystal.crystal_html.TextWithLinks] with the method's parameters.

        e.g. `(foo : Bar) : Baz`
        """
        # https://github.com/crystal-lang/crystal/pull/10109
        try:
            html = self.data["args_html"]
        except KeyError:
            html = self.data["args_string"]
        return crystal_html.parse_crystal_html(html)

    @cached_property
    def location(self) -> Optional[DocLocation]:
        """[Code location][mkdocstrings.handlers.crystal.items.DocLocation] of this method. Can be `None` if unknown."""
        # https://github.com/crystal-lang/crystal/pull/10122
        try:
            loc = self.data["location"]
        except KeyError:
            loc = None
            url = self.data.get("source_link")
            if url:
                regex = r"(?P<url>.+?/(?:blob|tree)/[^/]+/(?P<filename>.+)#L(?P<line>\d+))"
                m = re.fullmatch(regex, url)
                if m:
                    loc = m.groupdict()
        if loc:
            return self.root.update_url(
                DocLocation(loc["filename"], loc["line_number"], loc["url"])
            )


class DocInstanceMethod(DocMethod):
    """A [DocMethod][mkdocstrings.handlers.crystal.items.DocMethod] representing a Crystal instance method."""

    METHOD_SEP = METHOD_ID_SEP = "#"

    @property
    def kind(self) -> str:
        return "instance_method"


class DocClassMethod(DocMethod):
    """A [DocMethod][mkdocstrings.handlers.crystal.items.DocMethod] representing a Crystal class method."""

    METHOD_SEP = METHOD_ID_SEP = "."

    @property
    def kind(self) -> str:
        return "class_method"


class DocMacro(DocMethod):
    """A [DocMethod][mkdocstrings.handlers.crystal.items.DocMethod] representing a Crystal macro."""

    METHOD_ID_SEP = ":"

    @property
    def kind(self) -> str:
        return "macro"


class DocConstructor(DocClassMethod):
    """A [DocInstanceMethod][mkdocstrings.handlers.crystal.items.DocInstanceMethod] representing a Crystal macro."""


class DocMapping(Generic[D]):
    """Represents items contained within a type. A container of [DocItem][mkdocstrings.handlers.crystal.items.DocItem]s."""

    items: Sequence = ()
    search: Mapping[str, Any] = {}

    def __new__(cls, items: Sequence[D]) -> DocMapping:
        if not items:
            try:
                empty = cls._empty  # type: ignore
            except AttributeError:
                cls._empty = empty = object.__new__(cls)
            return empty
        return object.__new__(cls)

    def __init__(self, items: Sequence[D]):
        self.items = items
        self.search = search = {}
        for item in self.items:
            search.setdefault(item.rel_id, item)
            search.setdefault(item.name, item)

    def __iter__(self) -> Iterator[D]:
        """Iterate over the items like a list."""
        return iter(self.items)

    def __len__(self) -> int:
        """`len(mapping)` to get the number of items."""
        return len(self.items)

    def __bool__(self) -> bool:
        """`bool(mapping)` to check whether it's non-empty."""
        return bool(self.items)

    def __contains__(self, key: str) -> bool:
        """`"identifier" in mapping` to check whether the mapping contains an item by this identifier (see [DocItem.rel_id][mkdocstrings.handlers.crystal.items.DocItem.rel_id])."""
        return key in self.search

    def __getitem__(self, key: str) -> D:
        """`mapping["identifier"]` to get the item by this identifier (see [DocItem.rel_id][mkdocstrings.handlers.crystal.items.DocItem.rel_id]).

        Returns:
            A [DocItem][mkdocstrings.handlers.crystal.items.DocItem]
        Raises:
            KeyError: if the item is missing.
        """
        return self.search[key]

    def __add__(self, other: DocMapping) -> DocMapping:
        if not other:
            return self
        new = object.__new__(type(self))
        new.items = [*self, *other] if self else other.items
        new.search = collections.ChainMap(new.search, other.search)
        return new

    def __repr__(self):
        items = ", ".join(repr(item.rel_id) for item in self.items)
        return f"{type(self).__name__}{{{items}}}"


@dataclasses.dataclass
class DocLocation:
    """A location in code where an item was found."""

    filename: str
    """The absolute path to the file."""
    line: int
    """The (1-based) line number in the file."""
    url: Optional[str]
    """The derived URL of this location on a source code hosting site."""


class DocPath:
    """A path to a documentable Crystal item."""

    def __init__(self, data: Mapping[str, Any], root: DocType):
        self.data = data
        self.root = root

    @property
    def full_name(self) -> str:
        """The path of this item, e.g. `Foo::Bar(T)` or `baz`."""
        return self.data["full_name"]

    @property
    def abs_id(self) -> str:
        """The absolute identifier of this item, sometimes known as "path", e.g. `Foo::Bar` or `Foo::Bar#baz`."""
        return self.full_name.split("(", 1)[0]

    def lookup(self) -> DocItem:
        """[Look up][mkdocstrings.handlers.crystal.items.DocItem.lookup] this item in its originating doc structure.

        Raises:
            CollectionError: When an item by this identifier couldn't be found.
        """
        return self.root.lookup(self.abs_id)

    def __str__(self) -> str:
        """Convert to string -- same as `full_name`."""
        return self.full_name

    def __repr__(self) -> str:
        return repr(self.full_name)

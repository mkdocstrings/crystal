from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from mkdocstrings import BaseHandler, HandlerOptions

from . import inventory
from .collector import CrystalCollector
from .renderer import CrystalRenderer

__version__ = "0.3.8"


class CrystalHandler(CrystalCollector, CrystalRenderer, BaseHandler):
    name = "crystal"
    domain = "cr"
    load_inventory = staticmethod(inventory.list_object_urls)  # type: ignore[assignment]

    def __init__(
        self,
        theme: str,
        custom_templates: str | None = None,
        crystal_docs_flags: Sequence[str] = (),
        source_locations: Mapping[str, str] = {},
        **config: Any,
    ) -> None:
        BaseHandler.__init__(self, "crystal", theme, custom_templates)
        CrystalCollector.__init__(
            self, crystal_docs_flags=crystal_docs_flags, source_locations=source_locations
        )

    def get_options(self, local_options: Mapping[str, Any]) -> HandlerOptions:
        return {
            "nested_types": False,
            "file_filters": True,
            "show_source_links": True,
            "heading_level": 2,
            **local_options,
        }


get_handler = CrystalHandler

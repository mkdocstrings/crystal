from __future__ import annotations

from typing import Any, Mapping, Sequence

from mkdocstrings.handlers.base import BaseHandler

from . import inventory
from .collector import CrystalCollector
from .renderer import CrystalRenderer

__version__ = "0.3.7"


class CrystalHandler(CrystalCollector, CrystalRenderer, BaseHandler):
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


get_handler = CrystalHandler

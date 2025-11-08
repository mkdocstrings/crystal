from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING, Any

from mkdocstrings import BaseHandler, HandlerOptions

from . import inventory
from .collector import CrystalCollector
from .renderer import CrystalRenderer

if TYPE_CHECKING:
    from markdown import Extension
    from mkdocs.config.defaults import MkDocsConfig

__version__ = "0.3.9"


class CrystalHandler(CrystalCollector, CrystalRenderer, BaseHandler):
    name = "crystal"
    domain = "cr"
    load_inventory = staticmethod(inventory.list_object_urls)  # type: ignore[assignment]

    def __init__(
        self,
        *,
        theme: str,
        custom_templates: str | None = None,
        mdx: Sequence[str | Extension],
        mdx_config: Mapping[str, Any],
        handler_config: MutableMapping[str, Any],
        tool_config: MkDocsConfig,
    ) -> None:
        BaseHandler.__init__(
            self, theme=theme, custom_templates=custom_templates, mdx=mdx, mdx_config=mdx_config
        )
        CrystalCollector.__init__(
            self,
            **handler_config,
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

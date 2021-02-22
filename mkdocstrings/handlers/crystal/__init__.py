from typing import Any, Mapping, Optional, Sequence

from mkdocstrings.handlers.base import BaseHandler

from .collector import CrystalCollector
from .renderer import CrystalRenderer


class CrystalHandler(BaseHandler):
    pass


def get_handler(
    theme: str,
    custom_templates: Optional[str] = None,
    crystal_docs_flags: Sequence[str] = (),
    source_locations: Mapping[str, str] = (),
    **config: Any
) -> CrystalHandler:
    collector = CrystalCollector(
        crystal_docs_flags=crystal_docs_flags, source_locations=source_locations
    )
    renderer = CrystalRenderer("crystal", theme, custom_templates)
    renderer.collector = collector
    return CrystalHandler(collector, renderer)

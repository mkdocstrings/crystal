from typing import Any, Optional

from mkdocstrings.handlers.base import BaseHandler

from .collector import CrystalCollector
from .renderer import CrystalRenderer


class CrystalHandler(BaseHandler):
    pass


def get_handler(
    theme: str, custom_templates: Optional[str] = None, **config: Any
) -> CrystalHandler:
    collector = CrystalCollector()
    renderer = CrystalRenderer("crystal", theme, custom_templates)
    renderer.collector = collector
    return CrystalHandler(collector, renderer)

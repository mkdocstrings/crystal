import json
import re
import subprocess
from typing import Any, Optional

from markdown import Markdown

from mkdocstrings.handlers.base import BaseCollector, BaseHandler, BaseRenderer, CollectionError
from mkdocstrings.loggers import get_logger

log = get_logger(__name__)


class CrystalRenderer(BaseRenderer):
    fallback_theme = "material"

    default_config: dict = {
        "show_source": True,
        "heading_level": 2,
    }

    def render(self, data: Any, config: dict) -> str:
        final_config = dict(self.default_config)
        final_config.update(config)

        template = self.env.get_template(f"{data[0]}.html")

        heading_level = final_config.pop("heading_level")

        return template.render(
            config=final_config, obj=data[1], heading_level=heading_level, root=True,
        )

    def update_env(self, md: Markdown, config: dict) -> None:
        super().update_env(md, config)
        self.env.trim_blocks = True
        self.env.lstrip_blocks = True
        self.env.keep_trailing_newline = False


class CrystalCollector(BaseCollector):
    def __init__(self) -> None:
        self.json = json.loads(
            subprocess.check_output(
                [
                    "crystal",
                    "docs",
                    "--format=json",
                    "--project-name=",
                    "--project-version=",
                    "--source-refname=master",
                ],
            )
        )

    def collect(self, identifier: str, config: dict) -> Any:
        if not identifier.startswith("::"):
            identifier = "::" + identifier

        obj = ("program", self.json["program"])

        def find(*kinds):
            for kind in kinds:
                for t in obj[1][kind]:
                    if t["name"] == name:
                        return (kind.rstrip("s"), t)

        path = re.split(r"(\W+)", identifier)
        for sep, name in zip(path[1::2], path[2::2]):
            if sep == "::":
                obj = find("types", "constants")
            elif sep == ".":
                obj = find("class_methods", "constructors")
            elif sep == "#":
                obj = find("instance_methods")
            else:
                raise CollectionError(f"{identifier!r} - unknown separator {sep!r}")
            if obj is None:
                raise CollectionError(f"{identifier!r} - can't find {name!r}")

        return obj


class CrystalHandler(BaseHandler):
    pass


def get_handler(
    theme: str, custom_templates: Optional[str] = None, **config: Any
) -> CrystalHandler:
    return CrystalHandler(
        collector=CrystalCollector(), renderer=CrystalRenderer("crystal", theme, custom_templates),
    )

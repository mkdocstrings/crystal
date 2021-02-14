# mkdocstrings-crystal

**[Crystal][] language doc generator for [MkDocs][], via [mkdocstrings][].**

[![PyPI](https://img.shields.io/pypi/v/mkdocstrings-crystal)](https://pypi.org/project/mkdocstrings-crystal/)
[![GitHub](https://img.shields.io/github/license/oprypin/mkdocstrings-crystal)](LICENSE.md)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/oprypin/mkdocstrings-crystal/CI)](https://github.com/mkdocstrings/crystal/actions?query=event%3Apush+branch%3Amaster)

## Introduction

*mkdocstrings-crystal* allows you to insert API documentation (generated from [Crystal][]'s source code and doc comments) as part of any page on a [MkDocs][] site.

[See it in action][showcase].

To install it, run (possibly in a [virtualenv][]):

```shell
pip install mkdocstrings-crystal
```

**Continue to the [documentation site][].**

## Usage

With [MkDocs][], add/merge this base config as your _mkdocs.yml_:

```yaml
site_name: My Project

theme:
  name: material

plugins:
  - search
  - mkdocstrings:
      default_handler: crystal

markdown_extensions:
  - pymdownx.highlight
  - deduplicate-toc
```

Then, in any `docs/**/*.md` file, you can **mention a Crystal identifier alone on a line, after `:::`**:

```md
::: MyClass

::: Other::Class#some_method

::: Foo::CONSTANT
```

-- and in the output this will be replaced with generated API documentation for it, much like Crystal's own doc generator does.

This, of course, happens as part of a normal MkDocs build process:

```shell
mkdocs build  # generate from docs/ into site/
mkdocs serve  # live preview
```

**Continue to the [documentation site][].**


[crystal]: https://crystal-lang.org/
[mkdocs]: https://www.mkdocs.org/
[mkdocstrings]: https://mkdocstrings.github.io/
[virtualenv]: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment
[documentation site]: https://mkdocstrings.github.io/crystal/
[showcase]: https://mkdocstrings.github.io/crystal/showcase.html

# Quick-start guide

This assumes you already have some project in Crystal, say, a file `src/foo.cr`.

??? example "src/foo.cr"
    ```crystal
    --8<-- "examples/modern/src/foo.cr"
    ```

Hosting on GitHub is also assumed, though that's easy to adapt.

We'll be working from the project's root directory (the one that *contains* `src`).

[View the final file layout](https://github.com/oprypin/mkdocstrings-crystal/examples/modern/)

## Dependencies

The dependencies that we'll be using can be installed like this:

```console
$ pip install mkdocs-material mkdocstrings-crystal
```

This assumes you have [Python][] installed, with `pip` available.

!!! tip
    You might want to install these in a [virtualenv][] (i.e. localized just to this project).

!!! important
    Check out how to [manage Python dependencies](python-dependencies.md) long-term.

## Base config

Let's configure [MkDocs][] with *mkdocstrings-crystal*. Add/merge this config as your `mkdocs.yml`:

???+ example "mkdocs.yml"
    ```yaml
    --8<-- "examples/modern/mkdocs.yml"
    ```

???+ question "Why configure like this"
    [`pymdownx.*` extensions](https://facelessuser.github.io/pymdown-extensions/)
    :    Python-Markdown is an "old-school" Markdown parser, and these extensions bring the defaults more in line with what people are used to now.

    `deduplicate-toc` extension
    :    This is actually an integral part of *mkdocstrings-crystal*. [Read more](../extras.md#deduplicate-toc-extension).


!!! important
    The "literate-nav" plugin must appear *before* "section-index" in the list, because it overwrites the nav.


## View the site

That's it -- we're ready!

```shell
mkdocs build  # generate from docs/ into site/
mkdocs serve  # live preview
```

<!--If youmigrate.html#base-config-->

If you find that you have too many classes and you don't want to manually create files with callouts to them, there are ways to automate it, and good examples are in [the migration-oriented guide](migrate.md#base-config).


[mkdocs]: https://www.mkdocs.org/
[python]: https://www.python.org/
[virtualenv]: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment

# Quick-start guide

This assumes you already have some project in Crystal, say, a file `src/foo.cr`.

??? example "src/foo.cr"
    ```crystal
    --8<-- "examples/simple/src/foo.cr"
    ```

Hosting on GitHub is also assumed, though that's easy to adapt.

We'll be working from the project's root directory (the one that *contains* `src`).

[View the final file layout](https://github.com/oprypin/mkdocstrings-crystal/tree/master/examples/simple/)

## Dependencies

The dependencies that we'll be using can be installed like this:

```console
$ pip install mkdocs-material mkdocstrings-crystal
```

This assumes you have [Python][] installed, with `pip` available.

!!! tip
    You might want to install these in a [virtualenv][] (i.e. localized just to this project).

    And check out how to **[manage Python dependencies](python-dependencies.md)** long-term.

## Base config

Let's configure [MkDocs][] with *mkdocstrings-crystal*. Add/merge this config as your `mkdocs.yml`:

???+ example "mkdocs.yml"
    ```yaml
    --8<-- "examples/simple/mkdocs.yml"
    ```

???+ question "Why configure like this"
    `theme:` `material`
    :   [material](https://squidfunk.github.io/mkdocs-material/) is the only supported [MkDocs theme](https://www.mkdocs.org/user-guide/styling-your-docs/#third-party-themes).

    `repo_url` and `icon`
    :   Link back to your repository nicely. [See more](https://squidfunk.github.io/mkdocs-material/setup/adding-a-git-repository/).

    `extra_css`
    :   Don't forget to copy and include the [recommended styles](../styling.md#recommended-styles).

    `mkdocstrings:` `default_handler: crystal`
    :   Activate the upstream *mkdocstrings* plugin and tell it to collect items from Crystal, not Python, by default.

    `watch: [src]`
    :   Watch a directory for [auto-reload](https://pawamoy.github.io/mkdocstrings/usage/#watch-directories). Assuming the sources are under `src/`.

    [`pymdownx.*` extensions](https://facelessuser.github.io/pymdown-extensions/)
    :   Python-Markdown is an "old-school" Markdown parser, and these extensions bring the defaults more in line with what people are used to now.

    `deduplicate-toc` extension
    :   This is actually an integral part of *mkdocstrings-crystal*. [Read more](../extras.md#deduplicate-toc-extension).

## Add an API doc page

???+ example "docs/api.md"
    ```md
    --8<-- "examples/simple/docs/api.md"
    ```

## Add a normal page

???+ example "docs/index.md"
    ```md
    --8<-- "examples/simple/docs/index.md"
    ```

We linked directly to an identifier here, and *mkdocstrings* knows which page it's on and automatically links that. See: [identifier linking syntax](../README.md#identifier-linking-syntax).

## View the site

That's it -- we're ready!

```shell
mkdocs build  # generate from docs/ into site/
mkdocs serve  # live preview
```

## Next steps

If you find that you have too many classes and you don't want to manually create files with callouts to them, there are ways to automate it, and good examples are in [the migration-oriented guide](migrate.md#base-config).

Otherwise, you're encouraged to curate per-topic pages with your API items. See "Manually curated docs page" [in Showcase](../showcase.md#crystal-chipmunk) for examples.

And you'll probably want to [set up a navigation config](https://www.mkdocs.org/user-guide/configuration/#documentation-layout) anyway.


[mkdocs]: https://www.mkdocs.org/
[python]: https://www.python.org/
[virtualenv]: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment

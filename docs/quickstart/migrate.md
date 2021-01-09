# Migrating from Crystal's built-in doc generator

This assumes you already have some project in Crystal, say, a file `src/foo.cr`.

??? example "src/foo.cr"
    ```crystal
    --8<-- "examples/migrated/src/foo.cr"
    ```

Hosting on GitHub is also assumed, though that's easy to adapt.

We'll be working from the project's root directory (the one that *contains* `src`).

[View the final file layout](https://github.com/oprypin/mkdocstrings-crystal/examples/migrated/)

## Dependencies

The dependencies that we'll be using can be installed like this:

```console
$ pip install mkdocs-material mkdocstrings-crystal mkdocs-gen-files mkdocs-literate-nav mkdocs-section-index
```

This assumes you have [Python][] installed, with `pip` available.

!!! tip
    You might want to install these in a [virtualenv][] (i.e. localized just to this project). Otherwise, they go to `~/.local/lib/python*`.

!!! important
    Check out how to [manage Python dependencies](python-dependencies.md) long-term.

## Base config

Let's configure [MkDocs][] with *mkdocstrings-crystal*. Add/merge this config as your `mkdocs.yml`:

???+ example "mkdocs.yml"
    ```yaml
    --8<-- "examples/migrated/mkdocs.yml"
    ```

???+ question "Why configure like this"
    [`gen-files` plugin](https://github.com/oprypin/mkdocs-gen-files)
    :    Crystal's API generator automatically creates one HTML file per Crystal class. *mkdocstrings* doesn't do anything like that by itself, instead giving you the ability to [present a *story*](../README.md#introduction) and perhaps mention several items per page. However, in this guide we choose to do a 1:1 migration and don't want to manually create all those pages (e.g. a page `Foo/Bar/index.md` containing just `::: Foo::Bar`, so on and so on). [Continued](#generate-doc-stub-pages)

    [`literate-nav` plugin](https://github.com/oprypin/mkdocs-literate-nav)
    :    Right now it's not doing anything, we'll get back to it.

    [`section-index` plugin](https://github.com/oprypin/mkdocs-section-index)
    :    In Crystal's API doc sites we are used to having double functionality behind clicking an item in the left side navigation: it both opens a type's page and expands its sub-types. Well, in MkDocs world that's very much non-standard. But we bring that back with this plugin.

    `deduplicate-toc` extension
    :    This is actually an integral part of *mkdocstrings-crystal*. [Read more](../extras.md#deduplicate-toc-extension).

!!! important
    The "literate-nav" plugin must appear *before* "section-index" in the list, because it overwrites the nav.

## Generate doc stub pages

Add a script that will automatically populate a page for each type that exists in your project, with appropriate navigation. We're not populating the actual content, just inserting a small placeholder into each file for *mkdocstrings* to pick up.

???+ example "docs/gen_doc_stubs.py"
    ```python
    --8<-- "examples/migrated/docs/gen_doc_stubs.py"
    ```

This script is picked up to run seamlessly as part of the normal site build, because we had configured the [`gen-files` plugin](https://github.com/oprypin/mkdocs-gen-files), which is already explained above.

??? tip "More advanced examples of such scripts"
    * [In CrSFML](https://github.com/oprypin/crsfml/blob/master/tools/gen_doc_files.py)
    * [In Athena](https://github.com/oprypin/athena-website/blob/mkdocstrings/gen_doc_stubs.py)


## View the site

That's it -- we're ready!



```console
$ mkdocs build  # generate from docs/ into site/
$ mkdocs serve  # live preview
```



## Really preserving the URLs

We've been generating URLs such as `/Foo/Bar/` (really `/Foo/Bar/index.html`). But to actually keep all the URLs exactly like `crystal doc`'s site (for a non-breaking migration), we choose to make them look like `/Foo/Bar.html` instead.

Add this to the top of `mkdocs.yml`:

```yaml
use_directory_urls: false
```

But if you make this change by itself, MkDocs will no longer be able to group them into subsections nicely by default; it just doesn't see `/Foo.md` as the index page for the section containing `/Foo/*.md`, instead they'll be confusingly split into two.

So the navigation now has to be specified fully explicitly. As we've been generating the stub files, let's also generate the nav file itself. The file `docs/gen_doc_stubs.py` will gain these additions:

???+ example "docs/gen_doc_stubs.py"
    ```python hl_lines="10 15 21-22"
    --8<-- "examples/migrated/docs/gen_doc_stubs_nav.py"
    ```


[mkdocs]: https://www.mkdocs.org/
[python]: https://www.python.org/
[virtualenv]: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment

# Extras

## "deduplicate-toc" extension

For most [usages it is recommended](README.md#usage) to enable the "deduplicate-toc" Markdown extension, which comes bundled with *mkdocstrings-crystal*. It de-duplicates consecutive items that have the same title in the table of contents. This is important because Crystal can have multiple overloads of a method but in the ToC only their names are shown.

## "callouts" extension

*mkdocstrings-crystal* auto-enables the ["callouts" extension][] for Markdown (only within doc comments' content), so you can use that syntax instead of the common ["admonition" extension][]'s syntax.

!!! example "example.cr"
    ```crystal
    # Frobs the bar
    #
    # DEPRECATED: Use `baz` instead.
    def frob(bar)
    end
    ```

You can also enable that extension for the whole site:

!!! example "mkdocs.yml"
    ```yaml
    markdown_extensions:
      - callouts
    ```

["callouts" extension]: https://github.com/oprypin/markdown-callouts/
["admonition" extension]: https://python-markdown.github.io/extensions/admonition/

### Admonition styles

In addition to the [usual admonition styles](https://squidfunk.github.io/mkdocs-material/reference/admonitions/#supported-types), *mkdocstrings-crystal* injects styling for the Material theme to enable the following admonition kinds, used [in Crystal documentation](https://crystal-lang.org/reference/syntax_and_semantics/documenting_code.html#admonitions):

<style>
--8<-- "mkdocstrings/templates/crystal/material/style.css"

.admonition p>code {
    display: inline-block;
    width: 49%;
}
</style>

TODO: `TODO: ` `!!! todo`

NOTE: `NOTE: ` `!!! note`

BUG: `BUG: ` `!!! bug`

FIXME: `FIXME: ` `!!! fixme`

DEPRECATED: `DEPRECATED: ` `!!! deprecated`

OPTIMIZE: `OPTIMIZE: ` `!!! optimize`

Both the default styles and the extra styles work with both the ["callouts" extension][] (write them in all-uppercase) and the ["admonition" extension][] (write them in all-lowercase).

## Support for [MkDocs "macros" plugin](https://github.com/fralau/mkdocs_macros_plugin)

*Without* support, you have to access the doc root as

```jinja
{% set crystal = config['plugins']['mkdocstrings'].get_handler('crystal').collector.root %}
```

But instead you can use the convenience [pluglet](https://mkdocs-macros-plugin.readthedocs.io/en/latest/pluglets/) shipped with *mkdocstrings-crystal* to have such a `crystal` object available in every page *without* the above assignment.

!!! example "mkdocs.yml"
    ```yaml
    plugins:
      - macros:
          modules:
            - mkdocstrings_handlers.crystal.macros
    ```

Then you can dynamically generate Markdown based on introspecting Crystal's type tree. For example, instead of writing this in Markdown:

```md
These are the built-in mogrifier implementations:

* [Foo][MyModule::Mogrifiers::Foo]
* [Bar][MyModule::Mogrifiers::Bar]
* [Baz][MyModule::Mogrifiers::Baz]
...
```

you can just write:

```jinja
These are the built-in mogrifier implementations:

{% for typ in crystal.lookup('MyModule::Mogrifiers').types %}
  - [{{typ.name}}][{{typ.abs_id}}]
{% endfor %}
```

[Browse the API exposed by the root `DocType`](api.md).

## Support for [MkDocs "gen-files" plugin](https://oprypin.github.io/mkdocs-gen-files)

There's no special support, these just work well together.

The plugin exposes the MkDocs config, and from there you can get to the doc root:

```python
root = config['plugins']['mkdocstrings'].get_handler('crystal').collector.root
```

[Browse the API exposed by the root `DocType`](api.md).

From there, you can generate Markdown files based on introspecting Crystal's type tree. This usage is described [in the guide](quickstart/migrate.md#generate-doc-stub-pages).

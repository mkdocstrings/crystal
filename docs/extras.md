# Extras

## "deduplicate-toc" extension

For most [usages it is recommended](README.md#usage) to enable the "deduplicate-toc" Markdown extension, which comes bundled with *mkdocstrings-crystal*. It de-duplicates consecutive items that have the same title in the table of contents. This is important because Crystal can have multiple overloads of a method but in the ToC only their names are shown.

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
            - mkdocstrings.handlers.crystal.macros
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

## Support for [MkDocs "gen-files" plugin](https://github.com/oprypin/mkdocs-gen-files)

There's no special support, these just work well together.

The plugin exposes the MkDocs config, and from there you can get to the doc root:

```python
root = config['plugins']['mkdocstrings'].get_handler('crystal').collector.root
```

[Browse the API exposed by the root `DocType`](api.md).

From there, you can generate Markdown files based on introspecting Crystal's type tree. This usage is described [in the guide](quickstart/migrate.md#generate-doc-stub-pages).

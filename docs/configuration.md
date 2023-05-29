# Configuration

## Handler options

(See also: [*mkdocstrings* global options](https://mkdocstrings.github.io/usage/#global-options))

### `crystal_docs_flags:`

A list of command line arguments to pass to `crystal doc`. Mainly used to choose the source directories.

*The above option is global-only, while the ones below can also apply per-identifier.*

### `options:`

`nested_types:` (`true` / **`false`**)
:    Set to `true` to also recursively render all `Foo::Sub::Types` whenever rendering a given class `Foo`.

`file_filters:` [list of strings]
:    If a particular module spans over several files, you might want to choose to render only the sub-items (see `nested_types`) that came from a particular file. These patterns are regular expressions (not anchored) applied to the file path. Negating the patterns is done by starting it with `!` (which is then excluded from the following regex). This is very similar to [what's done in *mkdocstrings*](https://mkdocstrings.github.io/python/reference/mkdocstrings_handlers/python/handler/#mkdocstrings_handlers.python.handler.PythonHandler.default_config)

* `show_source_links:` (**`true`** / `false`)
:    Set to `false` to skip adding "*View source*" links after every method etc.

* `heading_level:` (`1`/**`2`**/`3`/`4`/`5`/`6`)
:    Each inserted identifier gets an HTML heading. The default heading is `<h2>`, and sub-headings in it are shifted accordingly (so if you write headings in doc comments, you're welcome to start with `#` `<h1>`). You can change this heading level, either the default one or per-identifier.

## Examples

!!! example "A global config (part of mkdocs.yml)"
    ```yaml
    plugins:
      - mkdocstrings:
          default_handler: crystal
          watch: [src]
          handlers:
            crystal:
              crystal_docs_flags:
                - src/bar.cr
                - lib/foo/src/foo.cr
              options:
                show_source_links: false
    ```

!!! example "A per-identifier config (a callout in a Markdown file)"
    ```md
    ::: SomeModule
        options:
          nested_types: true
          file_filters:
            - 'src/foo/[^/]+\.cr$'
          heading_level: 3
    ```

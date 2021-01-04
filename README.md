# mkdocstrings-crystal

Crystal language doc generator for [MkDocs][], via [mkdocstrings][].

[![PyPI](https://img.shields.io/pypi/v/mkdocstrings-crystal)](https://pypi.org/project/mkdocstrings-crystal/)
[![GitHub](https://img.shields.io/github/license/oprypin/mkdocstrings-crystal)](LICENSE.md)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/oprypin/mkdocstrings-crystal/CI)](https://github.com/oprypin/mkdocstrings-crystal/actions?query=event%3Apush+branch%3Amaster)

```shell
pip install mkdocstrings-crystal
```

[mkdocs]: https://www.mkdocs.org/
[mkdocstrings]: https://pawamoy.github.io/mkdocstrings/
[plugin]: https://www.mkdocs.org/user-guide/plugins/

## Introduction

Crystal has [its own easy-to-use generator of API documentation sites](https://crystal-lang.org/reference/using_the_compiler/#crystal-docs), but it's very rigid and doesn't attempt to do anything other than API documentation, so [these sites](https://crystal-lang.org/api/) end up being very isolated and prevent the author from presenting some kind of *story* about using their library.

Instead, this plugin is all about that *story*. It's very inspiring to look at [Python's documentation for `subprocess`](https://docs.python.org/3/library/subprocess.html), and hard to imagine a world in which this document is just an alphabetic dump of the functions in it.

So (matching the [idea behind *mkdocstrings*](https://pawamoy.github.io/mkdocstrings/usage/) but for Crystal), this allows you to just write textual documentation in Markdown and, in the middle of it, mention any identifier of a Crystal type, method etc., and get its signature, as well as doc comment, printed out right there.

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
      watch: [src]

markdown_extensions:
  - pymdownx.highlight
  - pymdownx.magiclink
  - pymdownx.saneheaders
  - pymdownx.superfences
  - deduplicate-toc
```

</details>

Then, in any `docs/**/*.md` file, you can **mention a Crystal identifier alone on a line, after `:::`**:

```markdown
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

### Identifier linking syntax

The syntax for these "callouts" is almost exactly the same as in Crystal's own doc comments. As you may also know, if you **mention an identifier in backticks within a doc comment (e.g. <code>\`SomeClass#some_method\`</code>)**, Crystal's doc generator will cross-link to it. The same also works seamlessly here, and you don't need to change anything (other than possible edge cases).

But another powerful feature of this plugin is that you can **[cross-reference](https://pawamoy.github.io/mkdocstrings/usage/#cross-references) items like this *anywhere* on the site**, not just in doc comments. But the syntax is **`[SomeClass#some_method][]`** instead. Or `[with custom text][SomeClass#some_method]`. Note, though, that currently this cross-reference syntax is quite rigid, and you need to specify the exact absolute identifier as *mkdocstrings-crystal* determines it. For that, you can click on the item in the navigation and copy the `#Anchor` that it points to (just drop the `#` part).

### Migrating from Crystal's own generator

Crystal's API generator creates one HTML file per Crystal class. If you don't care about this whole [*story* story](#introduction) and just want to unify your docs with a main MkDocs site, you're welcome to re-create such a file structure. The URLs can even be backwards-compatible.

Say, if you have a class `Foo::Bar`, you need to create a file _docs/Foo/Bar.md_ with the contents of just `::: Foo::Bar`. Repeat that for every class.

If you don't wish to write out such files manually, you can create them virtually, using [the **gen-files** plugin for MkDocs](https://github.com/oprypin/mkdocs-gen-files), with the following file *gen_doc_stubs.py*:

```python
import mkdocs_gen_files

root = mkdocs_gen_files.config['plugins']['mkdocstrings'].get_handler('crystal').collector.root

for typ in root.walk_types():
    filename = '/'.join(typ.abs_id.split('::')) + '.md'
    with mkdocs_gen_files.open(filename, 'w') as f:
        f.write(f'::: {typ.abs_id}\n\n')
```

You would also need this addition to _mkdocs.yml_:

```yaml
use_directory_urls: false

plugins:
  - gen-files:
      scripts:
        - gen_doc_stubs.py
```

Also check out [a more complex example](https://github.com/oprypin/athena-website/blob/mkdocstrings/gen_doc_stubs.py) and [an actual website using this](https://oprypin.github.io/athena-website/Validator/Constraint/).

## Usage details

We have been talking about seamlessly inserting Crystal documentation, but where is it coming from? The implementation actually still uses `crystal doc` generator but through [its JSON output](https://github.com/crystal-lang/crystal/pull/4746). So the requirement is the same: the source code that the doc comments and signatures are coming from is assumed to be somewhere under the _src/_ directory. If that isn't appropriate, you can select the wanted entry files by passing them to `crystal doc`, as part of [`crystal_docs_flags`](#crystal_docs_flags) ([example](https://github.com/oprypin/athena-website/blob/c06906d5933421120c76e15fd6f529eeb5c48221/mkdocs.yml#L33)).

### Options

(See also: [mkdocstrings global options](https://pawamoy.github.io/mkdocstrings/usage/#global-options))

#### `crystal_docs_flags:`

A list of command line arguments to pass to `crystal doc`. Mainly used to choose the source directories.

*The above options have been global-only, while the ones below can also apply per-identifier.*

#### `selection:`

* `nested_types:` (`true` / **`false`**)

  Set to `true` to also recursively render all `Foo::Sub::Types` whenever rendering a given class `Foo`.

* `file_filters:` [list of strings]

  If a particular module spans over several files, you might want to choose to render only the sub-items (see `nested_types`) that came from a particular file. These patterns ared regular expressions (not anchored) applied to the file path. Negating the patterns is done by starting it with `!` (which is then excluded from the following regex).

#### `rendering:`

* `show_source_links:` (**`true`** / `false`)

  Set to `false` to skip adding `[View source]` links after every method etc.

* `heading_level:`: (`1`/**`2`**/`3`/`4`/`5`/`6`)

  Each inserted identifier gets an HTML heading. The default heading is `<h2>`, and sub-headings in it are shifted accordingly (so if you write headings in doc comments, you're welcome to start with `#` `<h1>`). You can change this heading level, either the default one or per-identifier.

### Example of a global config

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
          rendering:
            show_source_links: false
```

### Example of a per-identifier config

```markdown
::: SomeModule
    selection:
      nested_types: true
      file_filters:
        - 'src/foo/[^/]+\.cr$'
    rendering:
      heading_level: 3
```

### Extras

#### "deduplicate-toc" extension

For most [usages it is recommended](#usage) to enable the "deduplicate-toc" Markdown extension, which comes bundled with mkdocstrings-crystal. It de-duplicates consecutive items that have the same title in the table of contents. This is useful because Crystal can have multiple overloads of a method but in the ToC only their names are shown.

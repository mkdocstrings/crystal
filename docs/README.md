# mkdocstrings-crystal

Crystal language doc generator for [MkDocs][], via [mkdocstrings][].

## Installation

```console
$ pip install mkdocstrings-crystal
```

[Continue with **quickstart**](quickstart/index.md).

## Introduction

Crystal has [its own easy-to-use generator of API documentation sites](https://crystal-lang.org/reference/using_the_compiler/#crystal-docs), but it's very rigid, as it doesn't attempt to do anything other than API documentation, so [these sites](https://crystal-lang.org/api/0.35.1/Process.html) end up being very isolated and prevent the author from presenting some kind of *story* about using their library.

Instead, this plugin is all about that *story*. It's very inspiring to look at [Python's documentation for `subprocess`](https://docs.python.org/3/library/subprocess.html), and hard to imagine a world in which this document is just an alphabetic dump of the functions in it.

So (matching the [idea behind *mkdocstrings*](https://pawamoy.github.io/mkdocstrings/usage/) but for Crystal), this allows you to just write textual documentation in Markdown and, in the middle of it, mention any identifier of a Crystal type, method etc., and have its API documentation (signature and doc comment) printed out right there.

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
  - deduplicate-toc
```

Then, in any `docs/**/*.md` file, you can **mention a Crystal identifier alone on a line, after `:::`**:

```md
::: MyClass

::: Other::Class#some_method

::: Foo::CONSTANT
```

-- and in the output this will be replaced with generated API documentation for it, much like Crystal's own doc generator does.

Learn more about this syntax: [in *mkdocstrings* in general](https://pawamoy.github.io/mkdocstrings/usage/) (Crystal specifics are below).

The auto-replacement, of course, happens as part of a normal MkDocs build process:

```console
$ mkdocs build  # generate from docs/ into site/
$ mkdocs serve  # live preview
```

### Identifier linking syntax

The syntax for these "callouts" is almost exactly the same as in Crystal's own doc comments. As you may also know, if you **mention an identifier in backticks within a doc comment (e.g. <code>\`SomeClass#some_method\`</code>)**, Crystal's doc generator will cross-link to it. The same also works seamlessly here, and you don't need to change anything (other than possible edge cases).

But another powerful feature of this plugin is that you can **[cross-reference](https://pawamoy.github.io/mkdocstrings/usage/#cross-references) items like this *anywhere* on the site**, not just in doc comments. But the syntax is **`[SomeClass#some_method][]`** instead. Or `[with custom text][SomeClass#some_method]`. Note, though, that currently this cross-reference syntax is quite rigid, and you need to specify the exact absolute identifier as *mkdocstrings-crystal* determines it. To find that out, you could click on the wanted item in the navigation and then copy the anchor part from the URL bar -- the part after (not including) `#`.

## Usage details

We have been talking about seamlessly inserting Crystal documentation, but where is it coming from? The implementation actually still uses `crystal doc` generator but through [its JSON output](https://github.com/crystal-lang/crystal/pull/4746). So the requirement is the same: the source code that the doc comments and signatures are coming from is assumed to be somewhere under the _src/_ directory. If that isn't appropriate, you can select the wanted entry files by passing them to `crystal doc`, as part of [`crystal_docs_flags`](configuration.md#crystal_docs_flags) (see "Custom source directories" [in Showcase](showcase.md#athena-framework)).

Continue to [Configuration](configuration.md).


[mkdocs]: https://www.mkdocs.org/
[mkdocstrings]: https://pawamoy.github.io/mkdocstrings/

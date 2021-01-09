# Troubleshooting

## Types aren't linkified in method signatures or aliases

This works, but you need to use a *nightly* build of Crystal. Crystal has some recent improvements that haven't made it into a release yet (as of 0.35). The plugin needs those improvements, otherwise it gracefully degrades.

If you have Crystal built locally, you might just `export PATH=/full/path/to/crystal/bin:$PATH` (as the plugin is hardcoded to use just `crystal`).

If you don't want to bother, you can opt to just use nightly Crystal [in CI, when the docs get auto-deployed](quickstart/ci.md) and assume that the links will work, even though you don't see them locally.

## The navigation sections look scattered

Perhaps it's because you made a page `Foo.md` and separately `Foo/Bar.md`. MkDocs just doesn't see them as related in any way.

[See also](quickstart/migrate.md#really-preserving-the-urls).

### Nav items are separated depending on if they have sub-items

In a deeply nested nav, it is best to stick to naming every file as `index.md` and making it the only one per directory. Then all items get treated equally during sorting. Or you can just define the `nav` yourself explicitly.

## The generated documentation does not look good

Note that only [mkdocs-material](https://squidfunk.github.io/mkdocs-material/) theme is supported.

You can always [customize the styles with CSS](styling.md), but make sure you've applied the default recommended style!

## MkDocs warns me about links to unfound documentation files

[See documentation of *mkdocstrings*](https://pawamoy.github.io/mkdocstrings/troubleshooting/#mkdocs-warns-me-about-links-to-unfound-documentation-files)

## Warning: could not find cross-reference target

[See documentation of *mkdocstrings*](https://pawamoy.github.io/mkdocstrings/troubleshooting/#warning-could-not-find-cross-reference-target)

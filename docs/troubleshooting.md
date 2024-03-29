# Troubleshooting

## Types aren't linkified in method signatures or aliases

Please make sure you're using the latest Crystal version - 0.36.0 at least. The plugin needs the included improvements, otherwise it gracefully degrades.

Even if you haven't managed to get that version of Crystal locally, you can just rely on [CI auto-deployment](quickstart/ci.md) and assume that the links will work, even though you won't see them locally.

## The navigation sections look scattered

Perhaps it's because you made a page `Foo.md` and separately `Foo/Bar.md`. MkDocs just doesn't see them as related in any way.

[See also](quickstart/migrate.md#really-preserving-the-urls).

### Nav items are separated depending on if they have sub-items

In a deeply nested nav, it is best to stick to naming every file as `index.md` and making it the only one per directory. Then all items get treated equally during sorting. Or you can just define the `nav` yourself explicitly.

## It takes too long to build the site

Yes, it's slow, especially for large codebases. The main thing, though, is that MkDocs was not optimized to handle sites with so so many pages. That is, [until I optimized it](https://github.com/mkdocs/mkdocs/pulls?q=is%3Apr+author%3Aoprypin+profile), but that hasn't made it into a release yet. Expect about a 2x speedup then. Or install the preview now:

```console
$ pip install -U git+https://github.com/mkdocs/mkdocs.git@refs/pull/2272/head
```

## The generated documentation does not look good

Note that only [mkdocs-material](https://squidfunk.github.io/mkdocs-material/) theme is supported.

You can always [customize the styles with CSS](styling.md), but make sure you've applied the default recommended style!

## MkDocs warns me about links to unfound documentation files

[See documentation of *mkdocstrings*](https://mkdocstrings.github.io/troubleshooting/#mkdocs-warns-me-about-links-to-unfound-documentation-files)

## Warning: could not find cross-reference target

[See documentation of *mkdocstrings*](https://mkdocstrings.github.io/troubleshooting/#warning-could-not-find-cross-reference-target)

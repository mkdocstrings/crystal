You can publish the website

```yaml  linenums="1" hl_lines="2 13 17 19 23"
--8<-- "examples/modern/.github/workflow/deploy-docs.yml"
```

???+ question "Why configure like this"
    Crystal Nightly is needed because this plugin relies on some improvements to Crystal's doc generator that haven't made it into a release yet.


!!! tip
    You can freely have a "dev" branch for working on docs that aren't ready for release yet. Then just merge it into the main one when ready.

!!! tip
    Your docs don't have to be in the same repository as the main code. In fact, the doc site can span several projects! See [Athena's website](https://github.com/oprypin/athena-website) as an example (of particular interest are `mkdocs.yml` (`crystal_docs_flags:`) and `shard*` files.

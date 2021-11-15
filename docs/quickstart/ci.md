# Continuous build and publishing

You can build and publish the website automatically on push using GitHub Pages and GitHub Actions. Here's our recommendation:

???+ example ".github/workflows/deploy-docs.yml"
    ```yaml  linenums="1" hl_lines="2 15 17 21"
    --8<-- "examples/simple/.github/workflows/deploy-docs.yml"
    ```

???+ question "Why configure like this"
    * Do *not* disable the workflow for non-*master* branches or pull requests. It is nice to ensure that the site builds (there can be errors!), instead at the bottom we prevent only the actual *deploy* action from being executed on non-*master*/non-*pushes*.
    * Dependencies are installed from `requirements.txt`. Make sure you've [populated it](python-dependencies.md).

TIP: You can freely have a "dev" branch for working on docs that aren't ready for release yet. Then just merge it into the main one when ready.

TIP: Your docs don't have to be in the same repository as the main code. In fact, the doc site can span several projects! See "Multi-repo setup" [in Showcase](../showcase.md#athena-framework).

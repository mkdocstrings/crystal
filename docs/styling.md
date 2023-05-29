## Recommended styles

Adding this styling to your site is recommended, otherwise things may not look right. You can, of course, adapt and add more.

!!! example "docs/css/mkdocstrings.css"
    ```css
    --8<-- "examples/simple/docs/css/mkdocstrings.css"
    ```

!!! example "mkdocs.yml"
    ```yaml
    extra_css:
      - css/mkdocstrings.css
    ```

This is in addition to the mandatory style that *mkdocstrings-crystal* already inserts (just for reference):

```css
--8<-- "mkdocstrings_handlers/crystal/templates/material/style.css"
```

## Custom styles

The doc items have consistently applied CSS classes. As of now, there is no separate documentation of what exactly they are. You are recommended to just *inspect* in the browser whenever you don't like the look of something and see how to reach it in CSS according to the markup.

The above example is some inspiration. Also check out [Showcase](showcase.md#tourmaline) for more.

import markupsafe
import pytest

from mkdocstrings_handlers.crystal import crystal_html


@pytest.mark.golden_test("crystal_html/**/*.yml")
def test_crystal_html(golden):
    code_html = crystal_html.parse_crystal_html(golden["crystal_code_html"])
    assert str(code_html) == golden.out["out_code"]
    assert [list(tok) for tok in code_html.tokens] == golden.out["out_tokens"]

    # print(pygments.highlight(code_html.text, pygments.lexers.get_lexer_by_name("crystal"), pygments.formatters.HtmlFormatter()))
    pygments_html = golden["pygments_code_html"]
    make_link = markupsafe.Markup('<a id="{}">{}</a>').format
    linkified_code_html = crystal_html.linkify_highlighted_html(
        pygments_html, code_html.tokens, make_link
    )
    assert str(linkified_code_html) == golden.out["out_linkified_code_html"]

import pytest

from mkdocstrings.handlers.crystal import renderer


@pytest.mark.golden_test("deduplicate_toc/**/*.yml")
def test_deduplicate_toc(golden):
    toc = list(golden["input"])
    renderer._deduplicate_toc(toc)
    assert toc == golden.out.get("output")

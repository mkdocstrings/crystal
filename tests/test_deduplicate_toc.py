import pytest

from mkdocstrings.handlers.crystal import deduplicate_toc


@pytest.mark.golden_test("deduplicate_toc/**/*.yml")
def test_deduplicate_toc(golden):
    toc = list(golden["input"])
    deduplicate_toc._deduplicate_toc(toc)
    assert toc == golden.out.get("output")

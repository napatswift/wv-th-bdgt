import pytest
from textextract import DocumentText


def test_should_raise_error_when_file_not_found():
    with pytest.raises(FileNotFoundError):
        DocumentText('fixtures/not-found.pdf')


def test_simple():
    text = DocumentText('test/text-extract/data/simple-thai-1page.pdf')
    pages = text.pages
    assert isinstance(pages, list)
    assert len(pages) == 1  # 1 page
    assert len(pages[0].lines) == 3  # 3 lines

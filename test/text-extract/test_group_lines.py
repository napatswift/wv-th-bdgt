from thbud.textextract.documenttext import group_text_by_line
from thbud.textextract.text import WordText


def test_empty_list():
    assert group_text_by_line([]) == []


def test_single_line():
    text_list = [WordText(0, 0, 0, 0, "Hello"), WordText(0, 0, 0, 0, "World")]
    assert group_text_by_line(text_list) == [[text_list[0], text_list[1]]]


def test_multiple_lines():
    text_list = [WordText(0, 0, 0, 0, "Hello"), WordText(0, 0, 0, 0, "World"),
                 WordText(0, 1, 0, 1.2, "Hello"), WordText(0, 1, 0, 1.2, "World")]

    assert group_text_by_line(text_list) == [
        [text_list[0], text_list[1]],
        [text_list[2], text_list[3]]
    ]


def test_large_threshold():
    text_list = [
        WordText(0, 0.0, 0, 0.0, "Word1"),
        WordText(0, 0.1, 0, 0.1, "Word2"),
        WordText(0, 1.0, 0, 1.1, "Word3"),
        WordText(0, 1.1, 0, 1.1, "Word4")
    ]

    lines = group_text_by_line(text_list, threshold=1)
    assert len(lines) == 1
    assert lines == [
        [text_list[0], text_list[1], text_list[2], text_list[3]]
    ]


def test_slighly_smaller_threshold():
    text_list = [
        WordText(0, 0.00, 0, 0.01, "Word1"),
        WordText(0, 0.05, 0, 0.051, "Word2"),
        WordText(0, 0.10, 0, 0.101, "Word3"),
        WordText(0, 0.15, 0, 0.151, "Word4")
    ]

    lines = group_text_by_line(text_list, threshold=0.049)
    assert len(lines) == 4
    assert lines == [
        [text_list[0]], [text_list[1]], [text_list[2]], [text_list[3]]
    ]

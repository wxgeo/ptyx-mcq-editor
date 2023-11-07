from ptyx_mcq_editor.lexer import get_all_tags


def test_get_all_tags():
    tags = get_all_tags()
    assert "IF" in tags
    assert "ANSWERS_LIST" in tags

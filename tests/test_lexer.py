from ptyx_mcq_editor.editor.lexer import get_all_tags


def test_get_all_tags():
    tags_with_python_arg, other_tags = get_all_tags()
    assert "IF" in tags_with_python_arg
    assert "ANSWERS_LIST" in tags_with_python_arg

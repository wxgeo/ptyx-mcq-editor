from ptyx.errors import ErrorInformation

from ptyx_mcq_editor.tools.python_code_tools import format_each_python_block, check_each_python_block


def test_ruff_formater():
    code = """Some text...

........
let a,b in 4..5
c=4
a=1/0
b=7
........

Some other text.

..............
def f(x,y):
 return x+y
......
"""
    target = """Some text...

............
let a, b in 4..5
c = 4
a = 1 / 0
b = 7
............

Some other text.

............
def f(x, y):
    return x + y
............
"""
    assert format_each_python_block(code) == target


def test_ruff_formater_for_invalid_python_code():
    # Test that invalid python code is left untouched.
    code = """Some text...

............
c = 4
if x:
b = 7
............

Other text.
"""
    assert format_each_python_block(code) == code


def test_ruff_checker():
    code = """
..........
let a,b
c = 4
a = 1 / 0
b = 7
def f(x):
return y
.........
    """
    assert check_each_python_block(code) == [
        ErrorInformation(
            type="SyntaxError",
            message="Expected an indented block after function definition",
            row=7,
            end_row=7,
            col=1,
            end_col=2,
            extra={"ruff-error-code": None},
        )
    ]

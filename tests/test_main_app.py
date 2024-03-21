import pytest

from ptyx_mcq_editor.app import main


def test_main_app():
    with pytest.raises(SystemExit):
        main(["--dry-run"])

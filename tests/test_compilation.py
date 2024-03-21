from multiprocessing import Queue
from pathlib import Path

from ptyx_mcq_editor.preview.compiler import PreviewCompilerWorker, compile_code


def test_compilation_error(tmp_path):
    c = PreviewCompilerWorker(
        "..............\nt=(4\n...........\n\n+ ok", doc_path=Path("tmp.ex"), doc_id=0, tmp_dir=tmp_path
    )
    return_data = c._generate()
    # noinspection PyUnresolvedReferences
    assert return_data["error"].info.message == "'(' was never closed"


def test_compil(tmp_path):
    code = "..............\nt=(4\n...........\n\n+ ok"
    queue = Queue()
    compile_code(queue, code=code, options={})

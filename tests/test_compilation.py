from multiprocessing import Queue
from pathlib import Path

from ptyx_mcq_editor.compilation.compiler import CompilerWorker, compile_code


def test_compilation_error(tmp_path):
    c = CompilerWorker("..............\nt=(4\n...........\n\n+ ok", Path("tmp.ex"), tmp_path)
    return_data = c._generate()
    # noinspection PyUnresolvedReferences
    assert return_data["error"].info.message == "'(' was never closed"


def test_compil(tmp_path):
    code = "..............\nt=(4\n...........\n\n+ ok"
    queue = Queue()
    compile_code(queue, code=code, options={})

#!/usr/bin/env python
# Copyright (c) 2021-2023 by Rocky Bernstein <rb@dustyfeet.com>

import click
import os
import sys

from xdis.codetype.base import iscode
from xdis.disasm import disco
from xdis.load import check_object_path, load_module
from xdis.op_imports import get_opcode_module
from xdis.version_info import IS_PYPY, PYTHON_VERSION_TRIPLE

from control_flow.augment_disasm import augment_instructions
from control_flow.bb import basic_blocks
from control_flow.cfg import ControlFlowGraph
from control_flow.dominators import DominatorTree, build_dom_set, dfs_forest
from control_flow.graph import write_dot
from control_flow.version import __version__

VARIANT = "pypy" if IS_PYPY else None


def control_flow(
    func_or_code,
    opc=None,
    code_version_tuple=PYTHON_VERSION_TRIPLE[:2],
    func_or_code_timestamp=None,
    func_or_code_name: str = "",
    debug: dict = {},
):
    """
    Compute control-flow graph, dominator information, and
    assembly instructions augmented with control flow for
    function "func".
    """

    if iscode(func_or_code):
        code = func_or_code
    else:
        code = func_or_code.__code__
        if func_or_code_name == "":
            func_or_code_name = func_or_code.__name__
    if func_or_code_name.startswith("<"):
        func_or_code_name = func_or_code_name[1:]
    if func_or_code_name.endswith(">"):
        func_or_code_name = func_or_code_name[:-1]

    print(func_or_code_name)

    disco(code_version_tuple, code, func_or_code_timestamp)

    if opc is None:
        opc = get_opcode_module(code_version_tuple, VARIANT)

    offset2inst_index = {}
    bb_mgr = basic_blocks(code, offset2inst_index, code_version_tuple)

    # for bb in bb_mgr.bb_list:
    #     print("\t", bb)

    cfg = ControlFlowGraph(bb_mgr)

    version = ".".join((str(n) for n in code_version_tuple[:2]))
    write_dot(func_or_code_name, f"/tmp/flow-{version}-", cfg.graph, write_png=True)

    try:
        dt = DominatorTree(cfg, debug.get("dom", False))

        cfg.dom_tree = dt.tree(False)
        dfs_forest(cfg.dom_tree, False)
        build_dom_set(cfg.dom_tree, False, debug.get("dom", False))
        write_dot(
            func_or_code_name, f"/tmp/flow-dom-{version}-", cfg.dom_tree, write_png=True
        )

        cfg.pdom_tree = dt.tree(True)
        dfs_forest(cfg.pdom_tree, True)
        build_dom_set(cfg.pdom_tree, True)
        write_dot(
            func_or_code_name,
            f"/tmp/flow-pdom-{version}-",
            cfg.pdom_tree,
            write_png=True,
        )

        print("=" * 30)
        augmented_instrs = augment_instructions(
            func_or_code, cfg, opc, offset2inst_index, bb_mgr
        )
        for inst in augmented_instrs:
            print(inst.disassemble(opc))
        # return cs_str
    except Exception:
        import traceback

        traceback.print_exc()
        print("Unexpected error:", sys.exc_info()[0])
        print(f"{func_or_code_name} had an error")


@click.command()
@click.version_option(version=__version__)
@click.argument("filename", type=click.Path(readable=True), required=True)
def main(filename):
    debug = {}
    try:
        # FIXME: add whether we want PyPy
        pyc_filename = check_object_path(filename)
        (
            version_tuple,
            timestamp,
            _,  # magic_int,
            co,
            _,  # is_pypy,
            _,  # source_size,
            _,  # sip_hash,
        ) = load_module(pyc_filename)

    except Exception:
        # Hack alert: we're using pyc_filename set as a proxy for whether the filename
        # exists.
        # check_object_path() will succeed if the file exists.
        stat = os.stat(filename)
        source = open(filename, "r").read()
        co = compile(source, filename, "exec")
        timestamp = stat.st_mtime
        version_tuple = PYTHON_VERSION_TRIPLE
    else:
        filename = pyc_filename

    name = co.co_name
    if name.startswith("<"):
        name = name[1:]
    if name.endswith(">"):
        name = name[:-1]

    control_flow(
        co,
        code_version_tuple=version_tuple,
        func_or_code_timestamp=timestamp,
        func_or_code_name=name,
        debug=debug,
    )


if __name__ == "__main__":
    main(sys.argv[1:])

#!/usr/bin/env python
# Copyright (c) 2021-2023 by Rocky Bernstein <rb@dustyfeet.com>

from typing import Optional
import os
import sys

from xdis.load import check_object_path, load_module
from xdis.magics import PYTHON_MAGIC_INT
from xdis.std import dis, opc
from xdis.version_info import IS_PYPY, PYTHON_VERSION_TRIPLE

from control_flow.augment_disasm import augment_instructions
from control_flow.bb import basic_blocks
from control_flow.cfg import ControlFlowGraph
from control_flow.dominators import DominatorTree, build_dom_set, dfs_forest
from control_flow.graph import write_dot


def main(func_or_code, name: str = ""):
    """
    Compute control-flow graph, dominator information, and
    assembly instructions augmented with control flow for
    function "func".
    """
    if name == "":
        if hasattr(func_or_code, "__name__"):
            name = func_or_code.__name__
        elif hasattr(func_or_code, "co_name"):
            name = func_or_code.co_name
        else:
            name = "unknown"
    if name.startswith("<"):
        name = name[1:]
    if name.endswith(">"):
        name = name[:-1]

    print(name)

    offset2inst_index = {}
    bb_mgr = basic_blocks(func_or_code, offset2inst_index)
    # for bb in bb_mgr.bb_list:
    #     print("\t", bb)

    dis(func_or_code)
    cfg = ControlFlowGraph(bb_mgr)

    version = ".".join((str(n) for n in sys.version_info[:2]))
    write_dot(name, f"/tmp/flow-{version}-", cfg.graph, write_png=True)

    try:
        dt = DominatorTree(cfg)

        cfg.dom_tree = dt.tree(False)
        dfs_forest(cfg.dom_tree, False)
        build_dom_set(cfg.dom_tree, False)
        write_dot(name, f"/tmp/flow-dom-{version}-", cfg.dom_tree, write_png=True)

        cfg.pdom_tree = dt.tree(True)
        dfs_forest(cfg.pdom_tree, True)
        build_dom_set(cfg.pdom_tree, True)
        write_dot(name, f"/tmp/flow-pdom-{version}-", cfg.pdom_tree, write_png=True)

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
        print(f"{name} had an error")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        try:
            # FIXME: add whether we want PyPy
            pyc_filename = check_object_path(filename)
            (
                version_tuple,
                timestamp,
                magic_int,
                co,
                is_pypy,
                source_size,
                sip_hash,
            ) = load_module(pyc_filename)

        except Exception:
            # Hack alert: we're using pyc_filename set as a proxy for whether the filename exists.
            # check_object_path() will succeed if the file exists.
            stat = os.stat(filename)
            source = open(filename, "r").read()
            co = compile(source, filename, "exec")
            is_pypy = IS_PYPY
            magic_int = PYTHON_MAGIC_INT
            sip_hash = 0
            source_size = stat.st_size
            timestamp = stat.st_mtime
            version_tuple = PYTHON_VERSION_TRIPLE
        else:
            filename = pyc_filename

        main(co)

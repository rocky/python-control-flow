#!/usr/bin/env python
# Copyright (c) 2021 by Rocky Bernstein <rb@dustyfeet.com>
from xdis.std import opc

from control_flow.augment_disasm import augment_instructions
from control_flow.bb import basic_blocks
from control_flow.cfg import ControlFlowGraph
from control_flow.dominators import DominatorTree, dfs_forest, build_dom_set
from control_flow.graph import write_dot

import dis
import os
import sys


def doit(fn, name=None):
    if not name:
        name = fn.__name__
    print(name)

    bb_mgr = basic_blocks(fn)
    # for bb in bb_mgr.bb_list:
    #     print("\t", bb)
    dis.dis(fn)
    cfg = ControlFlowGraph(bb_mgr)

    write_dot(name, "/tmp/flow-", cfg.graph, write_png=True)

    try:
        dt = DominatorTree(cfg)

        cfg.dom_tree = dt.tree(False)
        dfs_forest(cfg.dom_tree, False)
        build_dom_set(cfg.dom_tree, False)
        write_dot(name, "/tmp/flow-dom-", cfg.dom_tree, write_png=True)

        cfg.pdom_tree = dt.tree(True)
        dfs_forest(cfg.pdom_tree, True)
        build_dom_set(cfg.pdom_tree, True)
        write_dot(name, "/tmp/flow-pdom-", cfg.pdom_tree, write_png=True)

        print("=" * 30)
        augmented_instrs = augment_instructions(fn, cfg, opc.version_tuple)
        for inst in augmented_instrs:
            print(inst.disassemble(opc))
        # return cs_str
    except:
        import traceback

        traceback.print_exc()
        print("Unexpected error:", sys.exc_info()[0])
        print("%s had an error" % name)
        return ""


if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        exec(open(filename).read())
        short = os.path.basename(filename)[0:-3]
        doit(filename, short)

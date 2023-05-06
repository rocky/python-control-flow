#!/usr/bin/env python
# Copyright (c) 2021-2023 by Rocky Bernstein <rb@dustyfeet.com>
import os
import sys

from xdis.std import dis, opc

from control_flow.augment_disasm import augment_instructions
from control_flow.bb import basic_blocks
from control_flow.cfg import ControlFlowGraph
from control_flow.dominators import DominatorTree, build_dom_set, dfs_forest
from control_flow.graph import write_dot


def main(fn, name=None):
    if not name:
        name = fn.__name__
    print(name)

    offset2inst_index = {}
    bb_mgr = basic_blocks(fn, offset2inst_index)
    # for bb in bb_mgr.bb_list:
    #     print("\t", bb)
    dis(fn)
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
        augmented_instrs = augment_instructions(fn, cfg, opc, offset2inst_index, bb_mgr)
        for inst in augmented_instrs:
            print(inst.disassemble(opc))
        # return cs_str
    except Exception:
        import traceback

        traceback.print_exc()
        print("Unexpected error:", sys.exc_info()[0])
        print(f"{name} had an error")
        return ""


if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        exec(open(filename).read())
        short = os.path.basename(filename)[0:-3]
        main(filename, short)

#!/usr/bin/env python
from xdis.version_info import PYTHON_VERSION_TRIPLE, IS_PYPY
from xdis.std import opc

from control_flow.bb import basic_blocks
from control_flow.cfg import ControlFlowGraph
from control_flow.dominators import DominatorTree, dfs_forest, build_dom_set
from control_flow.augment_disasm import augment_instructions
from control_flow.structured_cf import build_control_structure

import dis
import os
import sys

def doit(fn, name=None):
    if not name:
        name = fn.__name__
    print(name)

    bb_mgr = basic_blocks(PYTHON_VERSION_TRIPLE, IS_PYPY, fn)
    for bb in bb_mgr.bb_list:
      print("\t", bb)
    dis.dis(fn)
    cfg = ControlFlowGraph(bb_mgr)
    dot_path = '/tmp/flow-%s.dot' % name
    png_path = '/tmp/flow-%s.png' % name
    open(dot_path, 'w').write(cfg.graph.to_dot(False))
    print("%s written" % dot_path)

    os.system("dot -Tpng %s > %s" % (dot_path, png_path))
    try:
        dt = DominatorTree(cfg)

        cfg.dom_tree = dt.tree(False)
        dfs_forest(cfg.dom_tree, False)
        build_dom_set(cfg.dom_tree, False)
        dot_path = '/tmp/flow-dom-%s.dot' % name
        png_path = '/tmp/flow-dom-%s.png' % name
        open(dot_path, 'w').write(cfg.dom_tree.to_dot())
        print("%s written" % dot_path)
        os.system("dot -Tpng %s > %s" % (dot_path, png_path))

        cfg.pdom_tree = dt.tree(True)
        dfs_forest(cfg.pdom_tree, True)
        build_dom_set(cfg.pdom_tree, True)
        dot_path = '/tmp/flow-pdom-%s.dot' % name
        png_path = '/tmp/flow-pdom-%s.png' % name
        open(dot_path, 'w').write(cfg.pdom_tree.to_dot())
        print("%s written" % dot_path)
        os.system("dot -Tpng %s > %s" % (dot_path, png_path))

        print('=' * 30)
        augmented_instrs = augment_instructions(fn, cfg, opc.version_tuple)
        for inst in augmented_instrs:
            print(inst.disassemble(opc))
        # print_structured_flow(fn, cfg, cfg.entry_node, cs_marks)
        # return cs_str
    except:
        import traceback
        traceback.print_exc()
        print("Unexpected error:", sys.exc_info()[0])
        print("%s had an error" % name)
        return ''

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        exec(open(filename).read())
        short = os.path.basename(filename)[0:-3]
        doit(filename, short)

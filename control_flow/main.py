#!/usr/bin/env python
from __future__ import print_function
from xdis import PYTHON_VERSION, IS_PYPY
from control_flow.bb import basic_blocks
from control_flow.cfg import ControlFlowGraph
from control_flow.dominators import DominatorTree, build_df, build_dom_set
from control_flow.structure import print_structured_flow, control_structure_short, print_cs_tree

import dis
import os
import sys

def doit(fn):
    name = fn.__name__
    print(name)


    bb_list = basic_blocks(PYTHON_VERSION, IS_PYPY, fn)
    for bb in bb_list:
      print("\t", bb)
    dis.dis(fn)
    cfg = ControlFlowGraph(bb_list)
    dot_path = '/tmp/flow-%s.dot' % name
    png_path = '/tmp/flow-%s.png' % name
    open(dot_path, 'w').write(cfg.graph.to_dot())
    print("%s written" % dot_path)

    os.system("dot -Tpng %s > %s" % (dot_path, png_path))
    try:
        cfg.dom_tree = DominatorTree(cfg).tree()

        build_df(cfg.dom_tree)
        build_dom_set(cfg.dom_tree)
        dot_path = '/tmp/flow-dom-%s.dot' % name
        png_path = '/tmp/flow-dom-%s.png' % name
        open(dot_path, 'w').write(cfg.dom_tree.to_dot())
        print("%s written" % dot_path)
        os.system("dot -Tpng %s > %s" % (dot_path, png_path))
        print('=' * 30)
        cs = control_structure_short(cfg, cfg.entry_node)
        print_cs_tree(cs)
        print('=' * 30)
        print_structured_flow(fn, cfg, cfg.entry_node)
    except:
        import traceback
        traceback.print_exc()
        print("Unexpected error:", sys.exc_info()[0])
        print("%s had an error" % name)

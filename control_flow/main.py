#!/usr/bin/env python
from __future__ import print_function
from xdis import PYTHON_VERSION, IS_PYPY
from control_flow.bb import basic_blocks
from control_flow.cfg import ControlFlowGraph
from control_flow.dominators import DominatorTree, build_df, build_dom_set
from control_flow.structured_cf import (
    print_structured_flow, build_control_structure, cs_tree_to_str
)

import dis
import os
import sys

def doit(fn, name):
    print(name)

    bb_mgr = basic_blocks(PYTHON_VERSION, IS_PYPY, fn)
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
        cfg.dom_tree = DominatorTree(cfg).tree()

        build_df(cfg.dom_tree)
        build_dom_set(cfg.dom_tree)
        dot_path = '/tmp/flow-dom-%s.dot' % name
        png_path = '/tmp/flow-dom-%s.png' % name
        open(dot_path, 'w').write(cfg.dom_tree.to_dot())
        print("%s written" % dot_path)
        os.system("dot -Tpng %s > %s" % (dot_path, png_path))
        print('=' * 30)
        cs  = build_control_structure(cfg, cfg.entry_node)
        cs_str = cs_tree_to_str(cs)
        print(cs_str)
        print('=' * 30)
        print_structured_flow(fn, cfg, cfg.entry_node)
        return cs_str
    except:
        import traceback
        traceback.print_exc()
        print("Unexpected error:", sys.exc_info()[0])
        print("%s had an error" % name)
        return ''

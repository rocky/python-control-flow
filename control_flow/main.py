#!/usr/bin/env python
from __future__ import print_function
from xdis import PYTHON_VERSION, IS_PYPY
from bb import basic_blocks
from cfg import ControlFlowGraph
from dominators import DominatorTree, build_df
from structure import print_structured_flow

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
        dom_tree = DominatorTree(cfg).tree()
        build_df(dom_tree)
        dot_path = '/tmp/flow-dom-%s.dot' % name
        png_path = '/tmp/flow-dom-%s.png' % name
        open(dot_path, 'w').write(dom_tree.to_dot())
        print("%s written" % dot_path)
        os.system("dot -Tpng %s > %s" % (dot_path, png_path))
        print_structured_flow(fn, dom_tree, bb_list)

        print('=' * 30)
    except:
        import traceback
        traceback.print_exc()
        print("Unexpected error:", sys.exc_info()[0])
        print("%s had an error" % name)

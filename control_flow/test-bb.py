#!/usr/bin/env python
from xdis import PYTHON_VERSION, IS_PYPY
from bb import basic_blocks
from cfg import ControlFlowGraph
from dominators import DominatorTree

import dis
import os

def five():
    return 5

def foo(a):
    if a:
        return 5
    else:
        return 6

def foo1(a):
    if a:
        a += 1
    else:
        a += 2
    return a

def bar(a):
    while True:
        if bar:
            return 5
        else:
            return 6

def baz(a):
    b = 0
    while a > 0:
        if a % 2:
          b += 1
        a >> 1
    return b

def for_break():
    for i in range(3):
        if i == 2:
            break
        else:
            continue

def try_finally():
    try:
        x = 1
    except RuntimeError:
        x = 2
    except:
        x = 3
    finally:
        x = 4
    return x

def try_no_finally():
    try:
        x = 1
    except RuntimeError:
        x = 2
    except:
        x = 3
    return x

def while_else(a):
    while a:
        a += 2
    else:
        return 6

def if_vs_and(a, b):
    if a \
       and b:
        c = 1
    if a:
        if b:
            c = 2
    return c

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
        dot_path = '/tmp/flow-dom-%s.dot' % name
        png_path = '/tmp/flow-dom-%s.png' % name
        open(dot_path, 'w').write(dom_tree.to_dot())
        print("%s written" % dot_path)
        os.system("dot -Tpng %s > %s" % (dot_path, png_path))
        print('=' * 30)
    except:
        print("%s had an error" % name)

doit(five)
doit(foo)
doit(foo1)
doit(bar)
doit(baz)
doit(for_break)
doit(try_finally)
doit(try_no_finally)
doit(while_else)
doit(if_vs_and)
doit(DominatorTree.tree)

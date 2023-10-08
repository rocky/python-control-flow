"""Test control_flow.bb: basic blocks and basd-block management"""
from typing import Callable

# from xdis.bytecode import get_instructions_bytes
# from xdis.std import opc
from control_flow.bb import basic_blocks
from control_flow.cfg import ControlFlowGraph
from control_flow.dominators import DominatorTree, dfs_forest, build_dom_set
from control_flow.graph import write_dot
from example_fns import two_basic_blocks, if_else_blocks

debug = False
if debug:
    import dis


def check_dom(fn: Callable, dt, cfg: ControlFlowGraph):
    return


def test_basic():
    offset2inst_index = {}
    for fn in (two_basic_blocks, if_else_blocks):
        name = fn.__name__
        if debug:
            print(name)
            dis.dis(fn)
            print()
        bb_mgr = basic_blocks(fn.__code__, offset2inst_index)
        cfg = ControlFlowGraph(bb_mgr)
        if debug:
            write_dot(name, "/tmp/test_dom-", cfg.graph, write_png=True)
        dt = DominatorTree(cfg)
        cfg.dom_tree = dt.tree(False)
        dfs_forest(cfg.dom_tree, False)
        build_dom_set(cfg.dom_tree, False)
        write_dot(name, "/tmp/test_dom-dom-", cfg.dom_tree, write_png=True)
        check_dom(fn, dt, cfg)


if __name__ == "__main__":
    test_basic()

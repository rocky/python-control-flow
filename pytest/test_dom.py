#!/usr/bin/env python
"""Test control_flow.bb: basic blocks and basd-block management"""

# from xdis.bytecode import get_instructions_bytes
# from xdis.std import opc
from control_flow.bb import basic_blocks
from control_flow.cfg import ControlFlowGraph
from control_flow.dominators import DominatorTree, dfs_forest, build_dom_set
from control_flow.graph import BB_ENTRY, write_dot
from example_fns import if_else_blocks, one_basic_block

DEBUG = True
if DEBUG:
    import dis


def check_dom(
    dom_tree: DominatorTree, check_dict: dict, fn_name: str, dead_code_count: int = 0
):

    # Prefix used in assert failures:
    prefix = f"In {fn_name}:"

    assert dom_tree.root, f"{prefix} tree should have non-null root"
    assert (
        BB_ENTRY in dom_tree.root.flags
    ), f"{prefix}: the root should be marked as an entry node"
    assert check_dict["count"] == len(dom_tree.doms) - dead_code_count
    assert (
        dom_tree.cfg.graph.nodes == dom_tree.root.dom_set
        ), f"{prefix} the root node should dominate all nodes"
    return


def test_basic():
    offset2inst_index = {}
    for fn, check_dict in (
        (one_basic_block, {"count": 2}),
        (if_else_blocks, {"count": 5}),
    ):
        name = fn.__name__
        if DEBUG:
            print(name)
            dis.dis(fn)
            print()
        bb_mgr = basic_blocks(fn.__code__, offset2inst_index)
        cfg = ControlFlowGraph(bb_mgr)
        if DEBUG:
            write_dot(name, "/tmp/test_dom-", cfg.graph, write_png=True)
        dom_tree = DominatorTree(cfg)
        cfg.dom_tree = dom_tree.tree(False)
        dfs_forest(cfg.dom_tree, False)
        build_dom_set(cfg.dom_tree, False)
        write_dot(name, "/tmp/test_dom-dom-", cfg.dom_tree, write_png=True)
        check_dom(dom_tree, check_dict, fn.__name__)


if __name__ == "__main__":
    test_basic()

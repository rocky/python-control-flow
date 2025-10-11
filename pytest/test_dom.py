#!/usr/bin/env python
"""Test dominiators"""

import pytest

# from xdis.bytecode import get_instructions_bytes
# from xdis.std import opc
from xdis import PYTHON_VERSION_TRIPLE

from python_control_flow.bb import basic_blocks
from python_control_flow.cfg import ControlFlowGraph
from python_control_flow.dominators import DominatorTree, dfs_forest, build_dom_set
from python_control_flow.graph import BB_ENTRY, write_dot
from example_fns import if_else_expr, one_basic_block

DEBUG = True
if DEBUG:
    import dis

python_version_tuple = PYTHON_VERSION_TRIPLE[:2]


@pytest.mark.skipif(
    PYTHON_VERSION_TRIPLE >= (3, 12), reason="Not gone over for Python 3.12 and above"
)
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

    # if python_version_tuple != (3, 12):
    #     assert (
    #         dom_tree.cfg.graph.nodes == dom_tree.root.dom_set +
    #         ), f"{prefix} the root node should dominate all nodes"
    # else:
    #     print("Investigate 3.12 exit domination")
    return


def test_basic():
    offset2inst_index = {}
    version = ".".join((str(n) for n in python_version_tuple))

    for fn, check_dict in (
        (one_basic_block, {"count": 1 if PYTHON_VERSION_TRIPLE >= (3, 12) else 2}),
        (
            if_else_expr,
            {
                "count": (
                    4
                    if PYTHON_VERSION_TRIPLE[:2] < (3, 11)
                    or PYTHON_VERSION_TRIPLE[:2] == (3, 12)
                    else 5
                )
            },
        ),
    ):
        name = fn.__name__
        if DEBUG:
            print(name)
            dis.dis(fn)
            print()
        # FIXME: add linestarts instead of None below
        bb_mgr = basic_blocks(fn.__code__, None, offset2inst_index)
        cfg = ControlFlowGraph(bb_mgr)
        if DEBUG:
            write_dot(name, f"/tmp/test_dom-{version}-", cfg.graph, write_png=True)
        dom_tree = DominatorTree(cfg)
        cfg.dom_tree = dom_tree.build_dom_tree()
        dfs_forest(cfg.dom_tree)
        build_dom_set(cfg.dom_tree, False)
        write_dot(name, f"/tmp/test_dom-dom-{version}-", cfg.dom_tree, write_png=True)
        check_dom(dom_tree, check_dict, fn.__name__)


if __name__ == "__main__":
    test_basic()

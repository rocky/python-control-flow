"""Test control_flow.cfg: control-flow graph"""

from typing import Callable
from xdis import PYTHON_VERSION_TRIPLE
from xdis.bytecode import get_instructions_bytes
from xdis.std import opc
from control_flow.bb import basic_blocks
from control_flow.cfg import ControlFlowGraph
from control_flow.graph import BB_ENTRY, write_dot
from example_fns import one_basic_block, if_else_expr

DEBUG = True
if DEBUG:
    import dis


def check_cfg(fn: Callable, cfg: ControlFlowGraph, check_dict: dict):
    """
    Check validity of congtrol-flow graph `cfg`. Values in `check_dict()`
    are used to assist.
    """
    bytecode = fn.__code__.co_code

    # Prefix used in assert failures:
    prefix = f"In {fn.__name__}:"

    assert cfg.entry_node, f"{prefix} control-flow-graph should have non-null entry"
    assert (
        BB_ENTRY in cfg.entry_node.flags
    ), f"{prefix}: the root should be marked as an entry node"

    assert (
        len(cfg.blocks) == check_dict["count"]
    ), f"{prefix} graph should have {check_dict['count']} blocks"

    # Check that all get_node returns the correct node
    # for all instruction offsets in bytecode
    current_block = cfg.offset2block[0]
    end_offset = current_block.bb.end_offset
    need_new_block = False
    offset2block = cfg.offset2block
    cached_offsets = len(offset2block)
    cache_diff = 0
    for inst in get_instructions_bytes(bytecode, opc):
        offset = inst.offset
        if need_new_block:
            current_block = offset2block[offset]
            end_offset = current_block.bb.end_offset
        if offset == end_offset:
            need_new_block = True
        else:
            # Increment number of entries added to cache after next cfg.get_node
            cache_diff += 1
            need_new_block = False

        assert current_block == cfg.get_node(offset)

    # Next check that all cfg.offset2block is populated
    # for all instruction offsets in bytecode as a result of
    # asking for each offset above
    assert all(
        (inst.offset in offset2block for inst in get_instructions_bytes(bytecode, opc))
    ), (f"{prefix}" "all offsets should be covered by cfg.offset2block")

    # Assert offset originally was in offset2block or was added in cache
    assert len(offset2block) == cached_offsets + cache_diff
    return


def test_basic():
    offset2inst_index = {}
    version = ".".join((str(n) for n in PYTHON_VERSION_TRIPLE[:2]))
    for fn, check_dict in (
        (one_basic_block, {"count": 2}),
        (if_else_expr, {"count": 4 if PYTHON_VERSION_TRIPLE[:2] != (3, 11) else 5}),
    ):
        if DEBUG:
            print(fn.__name__)
            dis.dis(fn)
            print()
        bb_mgr = basic_blocks(fn.__code__, offset2inst_index)
        cfg = ControlFlowGraph(bb_mgr)
        if DEBUG:
            write_dot(fn.__name__, f"/tmp/test_cfg-{version}-", cfg.graph, write_png=True)
        check_cfg(fn, cfg, check_dict)


if __name__ == "__main__":
    test_basic()

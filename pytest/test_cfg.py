"""Test control_flow.bb: basic blocks and basd-block management"""
from typing import Callable
from xdis.bytecode import get_instructions_bytes
from xdis.std import opc
from control_flow.bb import basic_blocks
from control_flow.cfg import ControlFlowGraph
from control_flow.graph import write_dot
from example_fns import two_basic_blocks, if_else_blocks

debug = True
if debug:
    import dis


def check_cfg(fn: Callable, cfg: ControlFlowGraph):
    bytecode = fn.__code__.co_code

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
    )

    # Assert offset originally was in offset2block or was added in cache
    assert len(offset2block) == cached_offsets + cache_diff
    return


def test_basic():
    for fn in (two_basic_blocks, if_else_blocks):
        if debug:
            print(fn.__name__)
            dis.dis(fn)
            print()
        bb_mgr = basic_blocks(fn)
        cfg = ControlFlowGraph(bb_mgr)
        if debug:
            write_dot(fn.__name__, "/tmp/test_cfg-", cfg.graph, write_png=True)
        check_cfg(fn, cfg)


if __name__ == "__main__":
    test_basic()

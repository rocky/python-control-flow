"""Test control_flow.bb: basic blocks and basic-block management"""

from control_flow.bb import basic_blocks, BB_ENTRY, BB_EXIT, BB_RETURN
from example_fns import one_basic_block, if_else_expr

DEBUG = True
if DEBUG:
    import dis


def check_blocks(bb_list: list, fn_name: str):
    assert (
        len(bb_list) >= 2
    ), "minimum basic block in a function is 2: entry and exception exit"

    prefix = f"In {fn_name}:"
    entry_count = 0
    exit_count = 0
    return_count = 0
    for bb in bb_list:
        if DEBUG:
            print(bb)
        if BB_ENTRY in bb.flags:
            entry_count += 1
        if BB_EXIT in bb.flags:
            exit_count += 1
            assert bb.start_offset == bb.end_offset
            assert bb.edge_count == 0
        if BB_RETURN in bb.flags:
            return_count += 1
        pass
    assert entry_count == 1
    assert exit_count == 1
    assert (
        return_count >= 1
    ), f"{prefix} expecting at least one block to be labeled a return"


def test_basic():

    offset2inst_index = {}
    for fn in (one_basic_block, if_else_expr):
        fn_name = fn.__name__
        if DEBUG:
            print(f"{fn_name}: ")
            dis.dis(fn)
            print()
        # FIXME: add linestarts instead of None below
        bb_mgr = basic_blocks(fn.__code__, None, offset2inst_index)
        check_blocks(bb_mgr.bb_list, fn_name)


if __name__ == "__main__":
    test_basic()

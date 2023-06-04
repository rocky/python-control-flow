"""Test control_flow.bb: basic blocks and basd-block management"""
from control_flow.bb import basic_blocks, BB_ENTRY, BB_EXIT, BB_RETURN
from example_fns import two_basic_blocks, if_else_blocks

debug = False
if debug:
    import dis


def check_blocks(bb_list: list):
    assert (
        len(bb_list) >= 2
    ), "minimum basic block in a function is 2: entry and exception exit"
    entry_count = 0
    exit_count = 0
    return_count = 0
    for bb in bb_list:
        if debug:
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
    assert return_count >= 1


def test_basic():

    offset2inst_index = {}
    for fn in (two_basic_blocks, if_else_blocks):
        if debug:
            print(fn.__name__)
            dis.dis(fn)
            print()
        bb_mgr = basic_blocks(fn.__code__, offset2inst_index)
        check_blocks(bb_mgr.bb_list)


if __name__ == "__main__":
    test_basic()

from graph import (BB_EXCEPT, BB_FINALLY, BB_FOR, BB_LOOP)
from xdis.std import get_instructions
def print_structured_flow(fn, dom_tree, bb_list):
    """Print structure skeleton"""
    print("\n" + ('-' * 40))

    offset2bb_start = {bb.start_offset: bb for bb in bb_list}
    offset2bb_end = {}
    setup_loop_target = set()
    for bb in bb_list:
        if not hasattr(bb, 'reach_offset'):
            # Dead code
            continue
        if bb.reach_offset not in offset2bb_end:
            print("reach_offset %d , bb #%d" % (bb.reach_offset, bb.number))
            offset2bb_end[bb.reach_offset] = [bb]
        else:
            # Smaller ranges (which appear later), go to
            # the front of the list
            offset2bb_end[bb.reach_offset].insert(0, bb)

    for inst in get_instructions(fn):
        offset = inst.offset
        if inst.opname == 'SETUP_LOOP':
            setup_loop_target.add(inst.argval)
        bb_start = offset2bb_start.get(offset, None)
        if bb_start:
            for flag in bb_start.flags:
                if flag == BB_LOOP:
                    print("LOOP")
                elif flag == BB_FOR:
                    print("FOR")
                elif flag == BB_FINALLY:
                    print("FINALLY")
                elif flag == BB_EXCEPT:
                    print("EXCEPT")
                    pass
                pass
            pass
        if offset in setup_loop_target:
            print("END_SETUP_LOOP")

        print(inst.disassemble())
        if offset in offset2bb_end:
            for bb in offset2bb_end[offset]:
                print("** dominator end for BB: #%s, start offset: %s, end offset: %d" %
                      (bb.number, bb.index[0], bb.reach_offset))
                pass
            pass
        pass
    return

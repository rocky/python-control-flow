from graph import (BB_EXCEPT, BB_FINALLY, BB_FOR, BB_LOOP)
from xdis.std import get_instructions
def print_structured_flow(fn, dom_tree, bb_list):
    """Print  structure skeleton"""
    print("\n" + ('-' * 40))

    bb_num = 0
    for bb in bb_list:
        bb.num = bb_num
        bb_num += 1

    offset2bb_start = {bb.start_offset: bb for bb in bb_list}
    offset2bb_end = {}
    for bb in bb_list:
        if not hasattr(bb, 'reach_offset'):
            # Dead code
            continue
        if bb.reach_offset not in offset2bb_end:
            offset2bb_end[bb.reach_offset] = [bb]
        else:
            offset2bb_end[bb.reach_offset].append(bb)

    for inst in get_instructions(fn):
        offset = inst.offset
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
        print(inst.disassemble())
        if offset in offset2bb_end:
            for bb in offset2bb_end[offset]:
                print("END of block range: BB num: %s" % (bb.num+1,))
    pass

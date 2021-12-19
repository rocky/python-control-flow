# Copyright (c) 2021 by Rocky Bernstein <rb@dustyfeet.com>
"""
Augment assembler instructions to include basic block and dominator information.
create a structured control flow graph.

This code is ugly.

"""
from __future__ import print_function
from xdis.std import get_instructions
from xdis.instruction import Instruction

# FIXME: this will be redone to use the result of cs_tree_to_str
def augment_instructions(fn, cfg, version_tuple):
    """Augment instructions in fn with dominator information"""
    current_block = cfg.entry_node

    dom_tree = cfg.dom_tree
    bb2dom_node = {node.bb:node for node in dom_tree.nodes}
    # block_stack = [current_block]

    starts = {current_block.start_offset: current_block}
    dom_reach_ends = {}
    ends = {current_block.end_offset: current_block}
    augmented_instrs = []
    offset = 0
    for inst in get_instructions(fn):
        offset = inst.offset
        bb = starts.get(offset, None)
        if bb:

            # FIXME: if a basic block is only its own dominator we don't have that
            # listed separately
            dom = bb2dom_node.get(bb, None)
            if dom:
                dom_number = dom.bb.number
                reach_ends = dom_reach_ends.get(dom.reach_offset, [])
                reach_ends.append(dom_number)
                dom_reach_ends[dom.reach_offset] = reach_ends
                pseudo_inst = Instruction("DOM_START", 1000, "pseudo", 0, dom_number,
                                          dom_number, f"Dominator {dom_number}",
                                          True, offset, None, False, False)
                augmented_instrs.append(pseudo_inst)

            pseudo_inst = Instruction("BB_START", 1001, "pseudo", 0, bb.number,
                                      bb.number, f"Basic Block {bb.number}",
                                      True, offset, None, False, False)
            augmented_instrs.append(pseudo_inst)
            if bb.follow_offset:
                follow_bb = cfg.offset2block[bb.follow_offset].bb
                starts[follow_bb.start_offset] = follow_bb
                ends[follow_bb.end_offset] = follow_bb
            for successor_bb in bb.successors:
                starts[successor_bb.start_offset] = successor_bb
                ends[successor_bb.end_offset] = successor_bb
        bb = ends.get(offset, None)
        augmented_instrs.append(inst)
        if bb:
            pseudo_inst = Instruction("BB_END", 1002, "pseudo", 0, bb.number,
                                      bb.number, f"Basic Block {bb.number}",
                                      True, offset, None, False, False)
            augmented_instrs.append(pseudo_inst)
        dom_list = dom_reach_ends.get(offset, None)
        if dom_list is not None:
            for dom_number in reversed(dom_list):
                pseudo_inst = Instruction("DOM_END", 1003, "pseudo", 0, dom_number,
                                          dom_number, f"Basic Block {dom_number}",
                                          True, offset, None, False, False)
                augmented_instrs.append(pseudo_inst)
            pass
        pass

    # We have a dummy bb at the end+1.
    # Add the end dominator info for that which should exist
    if version_tuple >= (3, 6):
        offset += 2
    else:
        offset += 1
    # FIXME: DRY with above
    dom_list = dom_reach_ends.get(offset, None)
    if dom_list is not None:
        for dom_number in reversed(dom_list):
            pseudo_inst = Instruction("DOM_END", 1003, "pseudo", 0, dom_number,
                                      dom_number, f"Basic Block {dom_number}",
                                      True, offset, None, False, False)
            augmented_instrs.append(pseudo_inst)
        pass

    return augmented_instrs

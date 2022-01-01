# Copyright (c) 2021 by Rocky Bernstein <rb@dustyfeet.com>
"""
Augment assembler instructions to include basic block and dominator information.

This code is ugly.

"""
from collections import namedtuple

from xdis.std import get_instructions
from xdis.instruction import Instruction

_ExtendedInstruction = namedtuple(
    "_Instruction",
    "opname opcode optype inst_size arg argval argrepr has_arg offset starts_line is_jump_target has_extended_arg basic_block dominator",
)
_ExtendedInstruction.opname.__doc__ = "Human readable name for operation"
_ExtendedInstruction.opcode.__doc__ = "Numeric code for operation"
_ExtendedInstruction.arg.__doc__ = (
    "Numeric argument to operation (if any), otherwise None"
)
_ExtendedInstruction.argval.__doc__ = (
    "Resolved arg value (if known), otherwise same as arg"
)
_ExtendedInstruction.argrepr.__doc__ = (
    "Human readable description of operation argument"
)
_ExtendedInstruction.has_arg.__doc__ = (
    "True if instruction has an operand, otherwise False"
)
_ExtendedInstruction.offset.__doc__ = (
    "Start index of operation within bytecode sequence"
)
_ExtendedInstruction.starts_line.__doc__ = (
    "Line started by this opcode (if any), otherwise None"
)
_ExtendedInstruction.is_jump_target.__doc__ = (
    "True if other code jumps to here, otherwise False"
)
_ExtendedInstruction.has_extended_arg.__doc__ = (
    "True there were EXTENDED_ARG opcodes before this, otherwise False"
)


class ExtendedInstruction(_ExtendedInstruction, Instruction):
    """Details for a bytecode operation

    Defined fields:
      opname - human readable name for operation
      opcode - numeric code for operation
      optype - opcode classification. One of
         compare, const, free, jabs, jrel, local, name, nargs
      inst_size - number of bytes the instruction occupies
      arg - numeric argument to operation (if any), otherwise None
      argval - resolved arg value (if known), otherwise same as arg
      argrepr - human readable description of operation argument
      has_arg - True opcode takes an argument. In that case,
                argval and argepr will have that value. False
                if this opcode doesn't take an argument. In that case,
                don't look at argval or argrepr.
      offset - start index of operation within bytecode sequence
      starts_line - line started by this opcode (if any), otherwise None
      is_jump_target - True if other code jumps to here,
                       'loop' if this is a loop beginning, which
                       in Python can be determined jump to an earlier offset.
                       Otherwise False
      has_extended_arg - True if the instruction was built from EXTENDED_ARG
                         opcodes
      fallthrough - True if the instruction can (not must) fall through to the next
                    instruction. Note conditionals are in this category, but
                    returns, raise, and unconditional jumps are not
      basic_block - extended basic block for this instruction
      dominator   - dominator of this instruction
    """

    def __str__(self):
        str = "ExtendedInstruction("
        if self.dominator and self.dominator.bb:
            str += f"dominator={self.dominator.bb.number}"
        bb_number = self.basic_block.number if self.basic_block else None
        if bb_number:
            str += f", BasicBlock=#{bb_number}"
        str += f", {self.opname}, opcode={self.opcode}, optype={self.optype}, offset={self.offset}, has_arg={self.has_arg}"

        if self.optype != "pseudo":
            str += f", has_arg={self.has_arg}"
            if self.has_arg:
                str += f''', arg={self.arg}, argval={self.argval}, argrepr="{self.argrepr}"'''
            # str += f", inst_size={self.inst_size}"
            if self.has_arg:
                str += f", has_arg = {self.has_arg}"
            if self.starts_line:
                str += f", self.starts_line={self.starts_line}"
            if self.is_jump_target:
                str += f", is_jump_target={self.is_jump_target}"
            if self.has_extended_arg:
                str += f", has_extended_arg={self.has_extended_arg}"
        str += ")"
        return str


# FIXME: this will be redone to use the result of cs_tree_to_str
def augment_instructions(fn, cfg, version_tuple):
    """Augment instructions in fn with dominator information"""
    current_block = cfg.entry_node

    dom_tree = cfg.dom_tree
    bb2dom_node = {node.bb: node for node in dom_tree.nodes}
    # block_stack = [current_block]

    starts = {current_block.start_offset: current_block}
    dom_reach_ends = {}
    ends = {current_block.end_offset: current_block}
    augmented_instrs = []
    bb = None
    dom = None
    offset = 0
    for inst in get_instructions(fn):
        offset = inst.offset
        new_bb = starts.get(offset, None)
        if new_bb:
            bb = new_bb
            # FIXME: if a basic block is only its own dominator we don't have that
            # listed separately
            new_dom = bb2dom_node.get(bb, dom)
            if new_dom is not None:
                dom = new_dom
            dom_number = dom.bb.number
            reach_ends = dom_reach_ends.get(dom.reach_offset, [])
            reach_ends.append(dom)
            dom_reach_ends[dom.reach_offset] = reach_ends
            pseudo_inst = ExtendedInstruction(
                "DOM_START",
                1000,
                "pseudo",
                0,
                dom_number,
                dom_number,
                f"Dominator {dom_number}",
                True,
                offset,
                None,
                False,
                False,
                bb,
                dom,
            )
            augmented_instrs.append(pseudo_inst)

            pseudo_inst = ExtendedInstruction(
                "BB_START",
                1001,
                "pseudo",
                0,
                bb.number,
                bb.number,
                f"Basic Block {bb.number}",
                True,
                offset,
                None,
                False,
                False,
                bb,
                dom,
            )
            augmented_instrs.append(pseudo_inst)
            if bb.follow_offset:
                follow_bb = cfg.offset2block[bb.follow_offset].bb
                starts[follow_bb.start_offset] = follow_bb
                ends[follow_bb.end_offset] = follow_bb
            for successor_bb in bb.successors:
                starts[successor_bb.start_offset] = successor_bb
                ends[successor_bb.end_offset] = successor_bb
                pass
            pass
        else:
            # Extend existing instruction

            # FIXME: this shouldn't be needed
            if bb is None:
                bb = dom.bb

            extended_inst = ExtendedInstruction(
                inst.opname,
                inst.opcode,
                inst.optype,
                inst.inst_size,
                inst.arg,
                inst.argval,
                inst.argrepr,
                inst.has_arg,
                inst.offset,
                inst.starts_line,
                inst.is_jump_target,
                inst.has_extended_arg,
                bb,
                dom,
            )
            augmented_instrs.append(extended_inst)
            pass

        bb = ends.get(offset, None)
        if bb:
            pseudo_inst = ExtendedInstruction(
                "BB_END",
                1002,
                "pseudo",
                0,
                bb.number,
                bb.number,
                f"Basic Block {bb.number}",
                True,
                offset,
                None,
                False,
                False,
                bb,
                dom,
            )
            augmented_instrs.append(pseudo_inst)
        dom_list = dom_reach_ends.get(offset, None)
        if dom_list is not None:
            for dom in reversed(dom_list):
                dom_number = dom.bb.number
                pseudo_inst = ExtendedInstruction(
                    "DOM_END",
                    1003,
                    "pseudo",
                    0,
                    dom_number,
                    dom_number,
                    f"Basic Block {dom_number}",
                    True,
                    offset,
                    None,
                    False,
                    False,
                    dom.bb,
                    dom,
                )
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
        for dom in reversed(dom_list):
            dom_number = dom.bb.number
            pseudo_inst = ExtendedInstruction(
                "DOM_END",
                1003,
                "pseudo",
                0,
                dom_number,
                dom_number,
                f"Basic Block {dom_number}",
                True,
                offset,
                None,
                False,
                False,
                dom.bb,
                dom,
            )
            augmented_instrs.append(pseudo_inst)
        pass

    # for inst in augmented_instrs:
    #     print(inst)
    return augmented_instrs

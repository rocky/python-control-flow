# Copyright (c) 2021-2024 by Rocky Bernstein <rb@dustyfeet.com>
"""
Augment assembler instructions to include basic block and dominator information.

This code is ugly.

"""
from copy import copy
from enum import IntEnum
from sys import maxsize
from types import CodeType
from typing import Any, Callable, Dict, NamedTuple, Optional, Union

from collections import defaultdict

from xdis.bytecode import Bytecode
from xdis.instruction import Instruction
from xdis.codetype.base import CodeBase

from control_flow.bb import BBMgr, BasicBlock
from control_flow.cfg import ControlFlowGraph
from control_flow.graph import Node, BB_FOR, BB_LOOP, BB_NOFOLLOW, ScopeEdgeKind


class JumpTarget(IntEnum):
    """
    Classifications of jump targets, which are used to create pseudo-ops before some
    (but not all) jump targets.

    This kind of classification simpilifies control flow parser
    matching.  In theory, it is not needed because we could either
    match on a set of previous instructions e.g. the set of RAISE,
    RETURN, YIELD instructions, or because we could create grammar for
    special kinds of statements that include the above,
    e.g. "no_follow_stmt" as a special kind of stmt.

    This was tried in uncompyle2, see "lastl_stmt".  The problem with
    this, is that the grammar then becomes more cumbersome and hard to
    understand, a lot of rules have to be duplicated: one contains
    "stmt" and one contains "lastl_stmt".  Or if "stmt ::=
    lastl_stmt", then a reduction rule needs to check when this isn't
    appropriate.  And there are many more grammar reductions for the
    additional but equivalent rules.

    So instead, by adding this as a pseudo op before parsing, parsing
    can make use of this without such additional rules for
    "lastl_stmt".

    Note: We don't mark explicitly fallthgough jump targets, or
    jump-back-to-loop-top targets.

    Here, the previous instructions are typically easy enough to match
    on via their instructions or a rule that groups together these
    instructions.

    The problems with doing this kind of thing for nofollow instructions like
    RETURN or RAISE is that these are more naturally part of a "stmt" rule
    so the single instruction isn't available for matching as part of control flow.
    But, again, if we add a pseudo op for these instructions, then that can be used
    in parse-based control-flow matching.

    """

    # The start of a loop
    LOOP = 2001

    # Comes after a NOFOLLOW_INSTRUCTIONS like a "return", "yield", "raise".
    # This does *not* include unconditional jumps as you would find in SIBLING,
    # or a jump to a loop.
    NOT_FALLEN_INTO = 2002

    # A sibling of the code bock that precedes this. You find this in alternate
    # code blocks. For example "if/else" where the target is the beginning of the
    # "else" that is jumped to after the end of an unconditional jump at the end of the
    # "then" the logical "end"
    SIBLING = 2003


block_kind2pseudo_op_name = {
    JumpTarget.LOOP: "LOOP",
    JumpTarget.NOT_FALLEN_INTO: "NOT_FALLEN_INTO_BLOCK",
    JumpTarget.SIBLING: "SIBLING_BLOCK",
}


class _ExtendedInstruction(NamedTuple):
    """Details for a bytecode operation

    The order of the fields below follows roughly how the values might be displayed
    in an assembly listing.

      is_jump_target: True if other code jumps to here,
                      'loop' if this is a loop beginning, which
                      in Python can be determined jump to an earlier offset.
                      Otherwise, False.

      starts_line: Optional Line started by this opcode (if any). Otherwise None.

      offset:  Start index of operation within bytecode sequence.

      opname:  human-readable name for operation.
      opcode:  numeric code for operation.

      has_arg:   True if opcode takes an argument. In that case,
                 ``argval`` and ``argepr`` will have that value. False
                 if this opcode doesn't take an argument. When False,
                 don't look at ``argval`` or ``argrepr``.

      arg:     Optional numeric argument to operation (if any). Otherwise, None.

      argval:  resolved arg value (if known). Otherwise, the same as ``arg``.
      argrepr: human-readable description of operation argument.

      tos_str:      If not None, a string representation of the top of the stack (TOS).
                    This is obtained by scanning previous instructions and
                    using information there and in their ``tos_str`` fields.

      positions: Optional dis.Positions object holding the start and end locations that
                 are covered by this instruction. This not implemented yet.

      optype:    Opcode classification. One of:
                    "compare", "const", "free", "jabs", "jrel", "local",
                    "name", or "nargs".

      inst_size: number of bytes the instruction occupies

      has_extended_arg: True if the instruction was built from EXTENDED_ARG
                        opcodes.

      fallthrough:  True if the instruction can (not must) fall through to the next
                    instruction. Note conditionals are in this category, but
                    returns, raise, and unconditional jumps are not.

      start_offset: if not None the instruction with the lowest offset that
                    pushes a stack entry that is consume by this opcode
    """

    # Numeric code for operation
    opcode: int

    # Human readable name for operation
    opname: str

    # Numeric operand value if operation has an operand, otherwise None.
    # This operand value is an index into one of the lists of a code type.
    # The exact table indexed depends on optype.
    arg: Optional[int]

    # Resolved operand value (if known). This is obtained indexing the appropriate list
    # indicated by optype using value arg.
    # If for some reason we can't extract a value this way ``argval`` has value as
    # ``arg``.
    argval: Any

    # String representation of argval if argval is not None.
    argrepr: str

    # Offset of the instruction
    offset: int

    starts_line: Optional[int]

    # True if other code jumps to here, the string "loop" if this is a loop
    # beginning, which in Python can be determined jump to an earlier
    # offset.  Otherwise, False.
    # Note that this is a generalization of Python's "is_jump_target".
    is_jump_target: Union[bool, str]

    # dis.Positions object holding the start and end locations that
    # are covered by this instruction.
    # FIXME: Implement. The below is just a placeholder.
    #
    positions: Optional[Any]

    # The following values are our own extended information not found (yet) #
    # in Python's Instruction structure.                                    #

    # First, values which can be computed or derived from the above,
    # along with an opcode structure. These We add these in an
    # instruction to make the instruction self sufficient.

    # opcode classification. One of:
    #   compare, const, free, jabs, jrel, local, name, nargs
    optype: str

    # True if instruction has an operand, otherwise False.
    has_arg: bool

    # The number of bytes this instruction consumes.
    inst_size: int

    # True there were EXTENDED_ARG opcodes before this, otherwise False
    has_extended_arg: Optional[bool] = None

    # True if the instruction can (not must) fall through to the next
    # instruction. Note conditionals are in this category, but
    # returns, raise, and unconditional jumps are not.
    fallthrough: Optional[bool] = None

    # If not None, a string representation of the top of the stack (TOS)
    tos_str: Optional[str] = None

    # Python expressions can be straight-line, operator like-basic block code that take
    # items off a stack and push a value onto the stack. In this case, in a linear scan
    # we can basically build up an expression tree.
    # Note this has to be the last field. Code to set this assumes this.
    start_offset: Optional[int] = None

    basic_block: BasicBlock = None
    dominator: Optional[Node] = None

EXTENDED_OPMAP = {
    "BB_END": 1001,
    "BB_START": 1002,
    "BREAK_FOR": 1003,
    "BREAK_LOOP": 1004,
    "BLOCK_END_JOIN": 1005,
    "JUMP_FOR": 1006,
    "JUMP_LOOP": 1007,
}
class ExtendedInstruction(_ExtendedInstruction, Instruction):
    """Details for an extended bytecode operation

    The order of the fields below follows roughly how the values might be displayed
    in an assembly listing.

      is_jump_target: True if other code jumps to here,
                      'loop' if this is a loop beginning, which
                      in Python can be determined jump to an earlier offset.
                      Otherwise, False.

      starts_line: Optional Line started by this opcode (if any). Otherwise None.

      offset:  Start index of operation within bytecode sequence.

      opname:  human-readable name for operation.
      opcode:  numeric code for operation.

      has_arg:   True if opcode takes an argument. In that case,
                 ``argval`` and ``argepr`` will have that value. False
                 if this opcode doesn't take an argument. When False,
                 don't look at ``argval`` or ``argrepr``.

      arg:     Optional numeric argument to operation (if any). Otherwise, None.

      argval:  resolved arg value (if known). Otherwise, the same as ``arg``.
      argrepr: human-readable description of operation argument.

      tos_str:      If not None, a string representation of the top of the stack (TOS).
                    This is obtained by scanning previous instructions and
                    using information there and in their ``tos_str`` fields.

      positions: Optional dis.Positions object holding the start and end locations that
                 are covered by this instruction. This not implemented yet.

      optype:    Opcode classification. One of:
                    "compare", "const", "free", "jabs", "jrel", "local",
                    "name", or "nargs".

      inst_size: number of bytes the instruction occupies

      has_extended_arg: True if the instruction was built from EXTENDED_ARG
                        opcodes.

      fallthrough:  True if the instruction can (not must) fall through to the next
                    instruction. Note conditionals are in this category, but
                    returns, raise, and unconditional jumps are not.

      start_offset: if not None the instruction with the lowest offset that
                    pushes a stack entry that is consume by this opcode

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


def post_ends(dom) -> set:
    """
    We only want to mark dominators that appear
    after some sort of "end" blocks or join condition.

    Why? In decompilation, we are trying to distinguish blocks that can
    start after an end of some compound, like "if", "try" or "for",
    from those blocks that are sibling or alternative blocks.

    Some examples:
        if b:
          sibling block
        elif
          sibling block
        else
          sibling block
        end
        post-end block

        try:
          sibling block
        except:
          sibling block
        else:
          sibling block
        end
        post-end block

        for ...
          sibling block
        else:
          sibling block
        end
        post-end block

        (condition and
            sibling condition and
            sibling condition or
            sibling condition)
        post-end block

    """

    if hasattr(dom, "pdom_set"):
        my_dom_set = dom.pdom_set
    else:
        my_dom_set = set()

    for prior_node in copy(my_dom_set):
        prior_bb = prior_node.bb
        if prior_bb == dom:
            # Don't list ourself in the prior_bb set that we dominate
            # ourselves if we don't fall through to the next block.
            # The grammar then will have to accommodate that we can
            # "if"s that have return blocks in the "then" part, and
            # it will have to decide how to treat what follows:
            # is this an "else" or not.  (Both are correct).
            # For chained assignments return (10 < b < 20) it feels
            # wrong to say that there is a block join after 10 < b as
            # opposed to a sibling kind of thing. This is I suppose
            # though a matter of taste.  Note that grammar has to
            # match what we do here in either case.
            if BB_NOFOLLOW in prior_node.flags:
                my_dom_set.remove(prior_node)
            continue
        if prior_bb.dom_set - my_dom_set:
            return set()
    return my_dom_set


# FIXME: this will be redone to use the result of cs_tree_to_str
def augment_instructions(
    fn_or_code: Union[Callable, CodeBase, CodeType],
    cfg: ControlFlowGraph,
    opc,
    offset2inst_index: Dict[int, int],
    bb_mgr: BBMgr,
):
    """Augment instructions in fn_or_code with dominator information"""
    current_block = cfg.entry_node

    dom_tree = cfg.dom_forest
    bb2dom_node = {node.bb: node for node in dom_tree.nodes}

    # version_tuple = opc.version_tuple
    # block_stack = [current_block]

    starts = {current_block.start_offset: current_block}
    dom_reach_ends = {}
    ends = {current_block.end_offset: current_block}
    augmented_instrs = []
    bb = None
    dom: Optional[Node] = None
    offset = 0
    loop_stack = []
    instructions = tuple(Bytecode(fn_or_code, opc).get_instructions(fn_or_code))

    # Compute offset2dom
    offset2bb: Dict[int, Node] = {bb.start_offset: bb for bb in bb_mgr.bb_list}

    # These are the kinds of jump instructions that we need to check
    # for non-end jump targets. It is basically an instruction with an
    # explicit jump target it in. (There are further conditions but those
    # are tested below when needed.)
    jump_instructions = bb_mgr.JUMP_INSTRUCTIONS | bb_mgr.JUMP_UNCONDITIONAL

    jump_target2offsets, jump_target_kind = find_jump_targets(
        opc, instructions, offset2inst_index, jump_instructions, bb_mgr
    )

    for inst in instructions:
        # Go through instructions inserting pseudo ops.
        # These are done for basic blocks, dominators,
        # and jump target locations.
        offset = inst.offset
        opname = inst.opname
        opcode = inst.opcode

        new_bb = starts.get(offset, None)
        if new_bb:
            bb = new_bb
            # FIXME: if a basic block is only its own dominator we don't have that
            # listed separately
            new_dom = bb2dom_node.get(bb, dom)
            if new_dom is not None:
                dom = new_dom
            # dom_number = dom.bb.number
            reach_ends = dom_reach_ends.get(dom.reach_offset, [])
            reach_ends.append(dom)
            dom_reach_ends[dom.reach_offset] = reach_ends

            if opcode in bb_mgr.FOR_INSTRUCTIONS or BB_LOOP in bb.flags:
                # Use the basic block of the block loop successor,
                # this is the main body of the loop, as the block to
                # check for leaving the loop.
                loop_block_dom_set = tuple(dom.bb.successors)[0].doms
                loop_stack.append((dom, loop_block_dom_set, inst))

            # For now we will assume that edges are sorted so in outermost-to-innermost nesting order.
            # Add any psuedo-token join markers
            if offset in cfg.offset2edges:
                for edge in reversed(cfg.offset2edges[offset]):
                    if edge.scoping_kind == ScopeEdgeKind.Join:
                        from_bb_number=edge.source.bb.number
                        pseudo_inst = ExtendedInstruction(
                            opname="BLOCK_END_JOIN",
                            opcode=EXTENDED_OPMAP["BLOCK_END_JOIN"],
                            optype="pseudo",
                            inst_size=0,
                            arg=from_bb_number,
                            argval=edge,
                            argrepr=f"from basic block #{from_bb_number}",
                            has_arg=True,
                            offset=offset,
                            starts_line=None,
                            is_jump_target=False,
                            has_extended_arg=False,
                            positions=None,
                            basic_block=bb,
                            dominator=dom,
                        )
                        augmented_instrs.append(pseudo_inst)


            pseudo_inst = ExtendedInstruction(
                opname="BB_START",
                opcode=EXTENDED_OPMAP["BB_START"],
                optype="pseudo",
                inst_size=0,
                arg=bb.number,
                argval=bb.number,
                argrepr=f"Basic Block {bb.number}",
                has_arg=True,
                offset=offset,
                starts_line=None,
                is_jump_target=False,
                has_extended_arg=False,
                positions=None,
                basic_block=bb,
                dominator=dom,
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
        elif bb is None:
            # FIXME: this shouldn't be needed
            bb = dom.bb

        if opcode in opc.JUMP_OPS:
            jump_target = inst.argval
            target_inst = instructions[offset2inst_index[jump_target]]
            target_bb = offset2bb[target_inst.offset]
            target_dom_set = target_bb.dom_set
            if inst.argval < offset:
                if opcode in bb_mgr.JUMP_UNCONDITIONAL:
                    # Classify backward loop jumps
                    pseudo_op_name = (
                        "JUMP_FOR"
                        if target_inst.opcode in bb_mgr.FOR_INSTRUCTIONS
                        else "JUMP_LOOP"
                    )
                    pseudo_inst = ExtendedInstruction(
                        opname=pseudo_op_name,
                        opcode=EXTENDED_OPMAP[pseudo_op_name],
                        optype="pseudo",
                        inst_size=0,
                        arg=target_dom_set,
                        argval=target_dom_set,
                        argrepr=f"{target_dom_set}",
                        has_arg=True,
                        offset=offset,
                        starts_line=None,
                        is_jump_target=False,
                        has_extended_arg=False,
                        positions=None,
                        basic_block=bb,
                        dominator=dom,
                    )
                    augmented_instrs.append(pseudo_inst)
            else:
                # Not backward jump, Note: if jump == offset, then we have an
                # infinite loop. We won't check for that here though.
                # Check for jump break out of a loop
                loop_related_jump = False
                if len(loop_stack) > 0:
                    # Check for loop-related jumps such as those that
                    # can occur from break, continue.  Note: we also
                    # add instructions for normal loop iteration jump
                    # and jump-termination jump
                    loop_dom, loop_block_dom_set, loop_inst = loop_stack[-1]
                    # SETUP_LOOP offsets in < 3.8 refer to places that
                    # that might not be jumped to by other instructions.
                    # The intervening instructions are stack cleanup like
                    # POP_STACK. We extend max to cover this kind of thing.
                    if jump_target >= max(
                        loop_dom.bb.__dict__["jump_offsets"] | {maxsize}
                    ):
                        if loop_inst.opcode in bb_mgr.FOR_INSTRUCTIONS:
                            pseudo_op_name = "BREAK_FOR"
                        else:
                            pseudo_op_name = "BREAK_LOOP"
                        pseudo_inst = ExtendedInstruction(
                            opname=pseudo_op_name,
                            opcode=EXTENDED_OPMAP[pseudo_op_name],
                            optype="pseudo",
                            inst_size=0,
                            arg=target_dom_set,
                            argval=target_dom_set,
                            argrepr=f"{target_dom_set}",
                            has_arg=True,
                            offset=offset,
                            starts_line=None,
                            is_jump_target=False,
                            has_extended_arg=False,
                            positions=None,
                            start_offset=None,
                            basic_block=bb,
                            dominator=dom,
                        )
                        augmented_instrs.append(pseudo_inst)
                        loop_related_jump = True
                        pass
                if not loop_related_jump:
                    # Mark conditional join jump instructions
                    print("FIXME: mark conditional join jump instructions")

                    # FIXME: complete...

                    # if jump_target == follow_bb_offset:
                    #     inst = ExtendedInstruction(
                    #         "JUMP_END_BLOCK",
                    #         1002,
                    #         "pseudo",
                    #         0,
                    #         target_dom_set,
                    #         target_dom_set,
                    #         f"{target_dom_set}",
                    #         True,
                    #         offset,
                    #         None,
                    #         False,
                    #         False,
                    #         bb,
                    #         dom,
                    #     )
                    #     augmented_instrs.append(pseudo_inst)
                    pass

        block_kind = jump_target_kind.get(offset)
        if block_kind is not None:
            pseudo_op_name = block_kind2pseudo_op_name[block_kind]
            pseudo_inst = ExtendedInstruction(
                opname=pseudo_op_name,
                opcode=int(block_kind),
                optype="pseudo",
                inst_size=0,
                arg=None,
                argval=None,
                argrepr="",
                has_arg=False,
                offset=offset,
                starts_line=None,
                is_jump_target=False,
                has_extended_arg=False,
                positions=None,
                start_offset=None,
                basic_block=bb,
                dominator=dom,
            )
            augmented_instrs.append(pseudo_inst)

        extended_inst = ExtendedInstruction(
            opname=opname,
            opcode=opcode,
            optype=inst.optype,
            inst_size=inst.inst_size,
            arg=inst.arg,
            argval=inst.argval,
            argrepr=inst.argrepr,
            has_arg=inst.has_arg,
            offset=inst.offset,
            starts_line=inst.starts_line,
            is_jump_target=inst.is_jump_target,
            has_extended_arg=inst.has_extended_arg,
            positions=None,
            start_offset=None,
            basic_block=bb,
            dominator=dom,
        )
        augmented_instrs.append(extended_inst)
        pass

        bb = ends.get(offset, None)
        if bb:
            pseudo_inst = ExtendedInstruction(
                opname="BB_END",
                opcode=EXTENDED_OPMAP["BB_END"],
                optype="pseudo",
                inst_size=0,
                arg=bb.number,
                argval=bb.number,
                argrepr=f"Basic Block {bb.number}",
                has_arg=True,
                offset=offset,
                starts_line=None,
                is_jump_target=False,
                has_extended_arg=False,
                positions=None,
                basic_block=bb,
                dominator=dom,
                start_offset=None,
            )
            augmented_instrs.append(pseudo_inst)
            if bb.flags in [BB_FOR, BB_LOOP]:
                loop_stack.pop()

        # dom_list = dom_reach_ends.get(offset, None)
        # if dom_list is not None:
        #     for dom in reversed(dom_list):
        #         dom_number = dom.bb.number
        #         post_end_set = post_ends(dom.bb)
        #         if post_end_set:
        #             pseudo_inst = ExtendedInstruction(
        #                 opname="BLOCK_END_JOIN",
        #                 opcode=1003,
        #                 optype="pseudo",
        #                 inst_size=0,
        #                 arg=dom_number,
        #                 argval=dom_number,
        #                 argrepr=f"Basic Block {post_end_set}",
        #                 has_arg=True,
        #                 offset=offset,
        #                 starts_line=None,
        #                 is_jump_target=False,
        #                 has_extended_arg=False,
        #                 positions=None,
        #                 start_offset=None,
        #                 basic_block=dom.bb,
        #                 dominator=dom,
        #             )
        #             augmented_instrs.append(pseudo_inst)
        #     pass
        # pass

    # # We have a dummy bb at the end+1.
    # # Add the end dominator info for that which should exist
    # if version_tuple >= (3, 6):
    #     offset += 2
    # else:
    #     offset += 1
    # # FIXME: DRY with above
    # dom_list = dom_reach_ends.get(offset, None)
    # if dom_list is not None:
    #     block_end_join_added = False
    #     for dom in reversed(dom_list):
    #         dom_number = dom.bb.number
    #         post_end_set = post_ends(dom.bb)
    #         if post_end_set and not block_end_join_added:
    #             pseudo_inst = ExtendedInstruction(
    #                 opname="BLOCK_END_JOIN_NO_ARG",
    #                 opcode=1003,
    #                 optype="pseudo",
    #                 inst_size=0,
    #                 arg=dom_number,
    #                 argval=dom_number,
    #                 argrepr=f"Basic Block {post_end_set}",
    #                 has_arg=False,
    #                 offset=offset,
    #                 starts_line=None,
    #                 is_jump_target=False,
    #                 has_extended_arg=False,
    #                 positions=None,
    #                 basic_block=dom.bb,
    #                 dominator=dom,
    #                 start_offset=None,
    #             )
    #             augmented_instrs.append(pseudo_inst)
    #             block_end_join_added = True
    #     pass

    # for inst in augmented_instrs:
    #     print(inst)
    return augmented_instrs


def find_jump_targets(
    opc,
    instructions,
    offset2inst_index: Dict[int, int],
    jump_instructions,
    bb_mgr,
    debug=False,
) -> Dict[int, list]:
    """
    Return a dictionary mapping jump-target offsets instruction offsets that
    jump to that target or precede it. We include fallthrough instructions
    Return the list of offsets.
    """

    jump_target2offsets: Dict[int, list] = defaultdict(list)
    for i, inst in enumerate(instructions):
        offset = inst.offset
        if inst.opcode in opc.JUMP_OPS:
            jump_target_offset = inst.argval
            jump_target2offsets[jump_target_offset].append(offset)

    jump_target_kind: Dict[int, bool] = {}
    # populate jump_target_kind based on the instruction and
    # possibly the previous instruction - the instruction whose offset comes just
    # before the instruction.
    for jump_target_offset, sources in jump_target2offsets.items():
        # Check if jump_target is in a loop
        if all(jump_target_offset < offset for offset in sources):
            jump_target_kind[jump_target_offset] = JumpTarget.LOOP
            continue

        inst_index = offset2inst_index[jump_target_offset]
        jump_target_sibling = True
        if inst_index > 0:
            prev_instruction = instructions[inst_index - 1]
            if prev_instruction.opcode in bb_mgr.NOFOLLOW_INSTRUCTIONS:
                jump_target_kind[jump_target_offset] = JumpTarget.NOT_FALLEN_INTO
                continue
            if prev_instruction.opcode not in bb_mgr.JUMP_UNCONDITIONAL:
                continue
            if (
                prev_instruction.opcode in jump_instructions
                and prev_instruction.argval < jump_target_offset
            ):
                continue
        if jump_target_sibling:
            jump_target_kind[jump_target_offset] = JumpTarget.SIBLING

    if debug:
        import pprint as pp

        pp.pprint(dict(jump_target2offsets))
        pp.pprint(jump_target_kind)

    return jump_target2offsets, jump_target_kind


def next_offset(offset: int, instructions: tuple, offset2inst_index: list):
    """
    Given an offset, a list of instructions, the basic block it is in,
    and a mapping of offsets to instructions,
    return the offset of the offset after instruction.

    For Python 3 this could be done by adding 2, for Python 2 it is either +1 or +3.
    However, by using instructions instead of bytecode, we eliminate Python version differences.
    """
    next_inst_index = offset2inst_index[offset] + 1
    return instructions[next_inst_index].offset

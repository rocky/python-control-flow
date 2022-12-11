#!/usr/bin/env python
# Copyright (c) 2021 by Rocky Bernstein <rb@dustyfeet.com>
import sys
from xdis import next_offset
from xdis.version_info import PYTHON3, PYTHON_VERSION_TRIPLE, IS_PYPY
from xdis.std import get_instructions
from xdis.op_imports import get_opcode_module
from control_flow.graph import (
    BB_POP_BLOCK,
    BB_SINGLE_POP_BLOCK,
    BB_STARTS_POP_BLOCK,
    BB_EXCEPT,
    BB_ENTRY,
    BB_TRY,
    BB_EXIT,
    BB_FINALLY,
    BB_END_FINALLY,
    BB_FOR,
    BB_BREAK,
    BB_JUMP_CONDITIONAL,
    BB_JUMP_UNCONDITIONAL,
    BB_JUMP_TO_FALLTHROUGH,
    BB_LOOP,
    BB_NOFOLLOW,
    BB_RETURN,
)

# The byte code versions we support
PYTHON_VERSIONS = (  # 1.5,
    # 2.1, 2.2, 2.3, 2.4, 2.5, 2.6,
    (2, 6),
    (2, 7),
    # 3.0, 3.1, 3.2, 3.3
    (3, 4),
    (3, 5),
    (3, 6),
    (3, 7),
    (3, 8),
    (3, 9),
    (3, 10),
)

end_bb = -1


# FIXME: The next version of xdis should include this. Use that.
def get_jump_val(jump_arg: int, version: tuple) -> int:
    return jump_arg * 2 if version[:2] >= (3, 10) else jump_arg


class BasicBlock(object):
    """Extended Basic block from the bytecode.

    An extended basic block is has a single entry. It can have multiple exits though,
    so it forms a tree with one one main trunk and jumps off of only this main trunk.
    A classic basic block ends in a single jump, conditional jump.

    The information in a basic block is a bit more than just the a
    continuous range of the bytecode offsets.

    It also contains:
      * jump-targets offsets,
      * exception-targets offsets,
      * flags that classify flow information in the block,
      * a graph node,
      * predecessor and successor sets, filled in a later phase
      * some layout information for dot graphing
      * a list of jump instructions that jump outside of loops
    """

    def __init__(
        self,
        start_offset,
        end_offset,
        follow_offset,
        loop_offset,
        flags=set(),
        jump_offsets=set(),
    ):

        global end_bb

        # The offset of the first and last instructions of the basic block.
        self.start_offset = start_offset
        self.end_offset = end_offset

        # The follow offset is just the offset that follows the last
        # offset of this basic block. It is None in the very last
        # basic block. Note that the the block that follows isn't
        # and "edge" from this basic block if the last instruction was
        # an unconditional jump or a return.
        # It is however useful to record this so that when we print
        # the flow-control graph, we place the following basic block
        # immediately below.
        self.follow_offset = follow_offset

        # Loops can start somewhere in the middle of the basic block.
        # FIXME: generalize to other kinds of instructions too?
        self.loop_offset = loop_offset

        # Jump offsets is the targets of all of the jump instructions
        # inside the basic block. Note that jump offsets can come from
        # things SETUP_.. operations as well as JUMP instructions
        self.jump_offsets = jump_offsets
        self.exception_offsets = set()

        # flags is a set of interesting bits about the basic block.
        # Elements of the bits are BB_... constants
        self.flags = flags
        self.index = (start_offset, end_offset)

        # Lists of predecessor and successor bacic blocks
        # This is computed in cfg.
        self.predecessors = set()
        self.successors = set()

        # List of blocks we dominiate is empty
        self.dom_set = set()

        # Set true if this is dead code, or unreachable
        self.unreachable = False
        self.number = end_bb
        self.edge_count = len(jump_offsets)
        if follow_offset is not None and not BB_NOFOLLOW in self.flags:
            self.edge_count += 1

        # List of instructions that break out of loops.
        # Of course, this is non-empty only when the basic block is inside a loop
        self.break_instructions = []

        end_bb += 1

    # A nice print routine for a Basic block
    def __repr__(self):
        if len(self.jump_offsets) > 0:
            jump_text = ", jumps=%s" % sorted(self.jump_offsets)
        else:
            jump_text = ""
        if len(self.exception_offsets) > 0:
            exception_text = ", exceptions=%s" % sorted(self.exception_offsets)
        else:
            exception_text = ""
        if len(self.flags) > 0:
            flag_text = ", flags=%s" % sorted(self.flags)
        else:
            flag_text = ""
        return "BasicBlock(#%d range: %s%s, follow_offset=%s, edge_count=%d%s%s)" % (
            self.number,
            self.index,
            flag_text,
            self.follow_offset,
            self.edge_count,
            jump_text,
            exception_text,
        )

    # Define "<" so we can compare and sort basic blocks.
    # Define 0 (the exit block) as the largest/last block
    def __lt__(self, other):
        self.number != 0 or self.number < other.number


class BBMgr(object):
    def __init__(self, version=PYTHON_VERSION_TRIPLE, is_pypy=IS_PYPY):
        global end_bb
        end_bb = 0
        self.bb_list = []
        self.exit_block = None

        version = tuple(version[:2])

        self.opcode = opcode = get_opcode_module(version)

        self.EXCEPT_INSTRUCTIONS = set([opcode.opmap["POP_TOP"]])
        self.FINALLY_INSTRUCTIONS = set([opcode.opmap["SETUP_FINALLY"]])
        self.FOR_INSTRUCTIONS = set([opcode.opmap["FOR_ITER"]])
        self.JABS_INSTRUCTIONS = set(opcode.hasjabs)
        self.JREL_INSTRUCTIONS = set(opcode.hasjrel)
        self.JUMP_INSTRUCTIONS = self.JABS_INSTRUCTIONS | self.JREL_INSTRUCTIONS
        self.JUMP_UNCONDITIONAL = set(
            [opcode.opmap["JUMP_ABSOLUTE"], opcode.opmap["JUMP_FORWARD"]]
        )

        self.POP_BLOCK_INSTRUCTIONS = set([opcode.opmap["POP_BLOCK"]])
        self.RETURN_INSTRUCTIONS = set([opcode.opmap["RETURN_VALUE"]])

        # These instructions don't appear in all version of Python
        self.BREAK_INSTRUCTIONS = set()
        self.END_FINALLY_INSTRUCTIONS = set()
        self.LOOP_INSTRUCTIONS = set()
        self.TRY_INSTRUCTIONS = set()
        self.END_FINALLY_INSTRUCTIONS = set()
        self.LOOP_INSTRUCTIONS = set()
        self.TRY_INSTRUCTIONS = set()

        if version < (3, 10):
            if version < (3, 8):
                self.BREAK_INSTRUCTIONS = set([opcode.opmap["BREAK_LOOP"]])
                self.LOOP_INSTRUCTIONS = set([opcode.opmap["SETUP_LOOP"]])
                self.TRY_INSTRUCTIONS = set([opcode.opmap["SETUP_EXCEPT"]])
            elif version < (3, 9):
                # FIXME: add WITH_EXCEPT_START
                self.END_FINALLY_INSTRUCTIONS = set([opcode.opmap["END_FINALLY"]])
                pass

        else:
            self.EXCEPT_INSTRUCTIONS = set([opcode.opmap["RAISE_VARARGS"]])

        if version >= (2, 6):
            self.JUMP_CONDITIONAL = set(
                [
                    opcode.opmap["POP_JUMP_IF_FALSE"],
                    opcode.opmap["POP_JUMP_IF_TRUE"],
                    opcode.opmap["JUMP_IF_FALSE_OR_POP"],
                    opcode.opmap["JUMP_IF_TRUE_OR_POP"],
                ]
            )
            self.NOFOLLOW_INSTRUCTIONS = set(
                [
                    opcode.opmap["RETURN_VALUE"],
                    opcode.opmap["YIELD_VALUE"],
                    opcode.opmap["RAISE_VARARGS"],
                ]
            )
            if "RERAISE" in opcode.opmap:
                self.NOFOLLOW_INSTRUCTIONS.add(opcode.opmap["RAISE_VARARGS"])

        # ??
        #                                   opcode.opmap['YIELD_VALUE'],
        #                                   opcode.opmap['RAISE_VARARGS']])

        if not PYTHON3:
            if version in ((2, 6), (2, 7)):
                # We classify intructions into various categories (even though
                # many of the below contain just one instruction). This can
                # isolate us from instruction changes in Python.
                # The classifications are used in setting basic block flag bits
                self.JUMP_UNCONDITIONAL = set(
                    [opcode.opmap["JUMP_ABSOLUTE"], opcode.opmap["JUMP_FORWARD"]]
                )
        else:
            self.JUMP_UNCONDITIONAL = set(
                [opcode.opmap["JUMP_ABSOLUTE"], opcode.opmap["JUMP_FORWARD"]]
            )

    def add_bb(
        self, start_offset, end_offset, loop_offset, follow_offset, flags, jump_offsets
    ):

        if BB_STARTS_POP_BLOCK in flags and start_offset == end_offset:
            flags.remove(BB_STARTS_POP_BLOCK)
            flags.add(BB_SINGLE_POP_BLOCK)

        block = BasicBlock(
            start_offset,
            end_offset,
            follow_offset,
            flags=flags,
            jump_offsets=jump_offsets,
            loop_offset=loop_offset,
        )
        self.bb_list.append(block)

        if BB_EXIT in flags:
            assert self.exit_block is None, "Should have only one exit"
            self.exit_block = block

        start_offset = end_offset
        flags = set([])
        jump_offsets = set([])
        return block, flags, jump_offsets


def basic_blocks(
    fn_or_code,
    offset2inst_index,
    version=PYTHON_VERSION_TRIPLE,
    is_pypy=IS_PYPY,
    more_precise_returns=False,
    print_instructions=False,
):
    """Create a list of basic blocks found in a code object.
    `more_precise_returns` indicates whether the RETURN_VALUE
    should modeled as a jump to the end of the enclosing function
    or not. See comment in code as to why this might be useful.
    """

    BB = BBMgr(version, is_pypy)

    # Get jump targets
    jump_targets = set()
    loop_targets = set()
    instructions = list(get_instructions(fn_or_code))
    for i, inst in enumerate(instructions):
        offset2inst_index[inst.offset] = i
        op = inst.opcode
        offset = inst.offset
        follow_offset = next_offset(op, BB.opcode, offset)
        if op in BB.JUMP_INSTRUCTIONS:
            jump_value = get_jump_val(inst.arg, version)
            if op in BB.JABS_INSTRUCTIONS:
                jump_offset = jump_value
            else:
                jump_offset = follow_offset + jump_value

            # For Python so far, a loop jump always goes from a
            # larger offset to a smaller one
            is_loop = jump_offset <= inst.offset
            if is_loop:
                loop_targets.add(jump_offset)
            jump_targets.add(jump_offset)
            pass

    # Add an artificial block where we can link the exits of other blocks
    # to. This helps when there is a "raise" not in any try block and
    # in computing reverse dominators.
    end_offset = instructions[-1].offset
    if version >= (3, 6):
        end_bb_offset = end_offset + 2
    else:
        end_bb_offset = end_offset + 1

    end_block, _, _ = BB.add_bb(
        end_bb_offset, end_bb_offset, None, None, set([BB_EXIT]), []
    )

    start_offset = 0
    end_offset = -1
    jump_offsets = set()
    prev_offset = -1
    endloop_offsets = [-1]
    flags = set([BB_ENTRY])
    end_try_offset_stack = []
    try_stack = [end_block]
    end_try_offset = None
    loop_offset = None
    return_blocks = []

    for i, inst in enumerate(instructions):
        if print_instructions:
            print(inst)
        prev_offset = end_offset
        end_offset = inst.offset
        op = inst.opcode
        offset = inst.offset
        follow_offset = next_offset(op, BB.opcode, offset)

        if offset == end_try_offset:
            if len(end_try_offset_stack):
                end_try_offset = end_try_offset_stack[-1]
                end_try_offset_stack.pop()
            else:
                end_try_offset = None

        if op in BB.LOOP_INSTRUCTIONS:
            jump_offset = follow_offset + inst.arg
            endloop_offsets.append(jump_offset)
            loop_offset = offset
        elif offset == endloop_offsets[-1]:
            endloop_offsets.pop()
        pass

        if op in BB.LOOP_INSTRUCTIONS:
            flags.add(BB_LOOP)
        elif op in BB.BREAK_INSTRUCTIONS:
            flags.add(BB_BREAK)
            jump_offsets.add(endloop_offsets[-1])
            block, flags, jump_offsets = BB.add_bb(
                start_offset,
                end_offset,
                loop_offset,
                follow_offset,
                flags,
                jump_offsets,
            )
            loop_offset = None
            if BB_TRY in block.flags:
                try_stack.append(block)
            start_offset = follow_offset

        if offset in jump_targets:
            # Fallthrough path and jump target path.
            # This instruction definitely starts a new basic block
            # Close off any prior basic block
            if start_offset < end_offset:
                block, flags, jump_offsets = BB.add_bb(
                    start_offset,
                    prev_offset,
                    loop_offset,
                    end_offset,
                    flags,
                    jump_offsets,
                )
                loop_offset = None
                if BB_TRY in block.flags:
                    try_stack.append(block)
                    pass

                start_offset = end_offset
                pass
            if offset in loop_targets:
                flags.add(BB_LOOP)

        # Add block flags for certain classes of instructions
        if op in BB.JUMP_CONDITIONAL:
            flags.add(BB_JUMP_CONDITIONAL)

        if op in BB.POP_BLOCK_INSTRUCTIONS:
            flags.add(BB_POP_BLOCK)
            if start_offset == offset:
                flags.add(BB_STARTS_POP_BLOCK)
                flags.remove(BB_POP_BLOCK)
        elif op in BB.EXCEPT_INSTRUCTIONS:
            if sys.version_info[0:2] <= (2, 7):
                # In Python up to 2.7, thre'POP_TOP'S at the beginning of a block
                # indicate an exception handler. We also check
                # that we are nested inside a "try".
                if len(try_stack) == 0 or start_offset != offset:
                    continue
                pass
                if (
                    instructions[i + 1].opcode != BB.opcode.opmap["POP_TOP"]
                    or instructions[i + 2].opcode != BB.opcode.opmap["POP_TOP"]
                ):
                    continue
            flags.add(BB_EXCEPT)
            try_stack[-1].exception_offsets.add(start_offset)
            pass
        elif op in BB.TRY_INSTRUCTIONS:
            end_try_offset_stack.append(inst.argval)
            flags.add(BB_TRY)
        elif op in BB.END_FINALLY_INSTRUCTIONS:
            flags.add(BB_END_FINALLY)
            try_stack[-1].exception_offsets.add(start_offset)
        elif op in BB.FOR_INSTRUCTIONS:
            flags.add(BB_FOR)
            jump_offsets.add(inst.argval)
            block, flags, jump_offsets = BB.add_bb(
                start_offset,
                end_offset,
                loop_offset,
                follow_offset,
                flags,
                jump_offsets,
            )
            loop_offset = None
            start_offset = follow_offset
        elif op in BB.JUMP_INSTRUCTIONS:
            # Some sort of jump instruction.
            # Figure out where we jump to amd add it to this
            # basic block's jump offsets.
            jump_offset = inst.argval

            jump_offsets.add(jump_offset)
            if op in BB.JUMP_UNCONDITIONAL:
                flags.add(BB_JUMP_UNCONDITIONAL)
                if jump_offset == follow_offset:
                    flags.add(BB_JUMP_TO_FALLTHROUGH)
                    pass
                block, flags, jump_offsets = BB.add_bb(
                    start_offset,
                    end_offset,
                    loop_offset,
                    follow_offset,
                    flags,
                    jump_offsets,
                )
                loop_offset = None
                if BB_TRY in block.flags:
                    try_stack.append(block)
                    pass

                start_offset = follow_offset
            elif version[:2] < (3, 10) or op != BB.opcode.SETUP_LOOP:
                if op in BB.FINALLY_INSTRUCTIONS:
                    flags.add(BB_FINALLY)

                block, flags, jump_offsets = BB.add_bb(
                    start_offset,
                    end_offset,
                    loop_offset,
                    follow_offset,
                    flags,
                    jump_offsets,
                )
                loop_offset = None
                if BB_TRY in block.flags:
                    try_stack.append(block)
                start_offset = follow_offset

                pass
        elif op in BB.NOFOLLOW_INSTRUCTIONS:
            flags.add(BB_NOFOLLOW)
            if op in BB.RETURN_INSTRUCTIONS:
                flags.add(BB_RETURN)

            last_block, flags, jump_offsets = BB.add_bb(
                start_offset,
                end_offset,
                loop_offset,
                follow_offset,
                flags,
                jump_offsets,
            )
            loop_offset = None
            start_offset = follow_offset
            if op in BB.RETURN_INSTRUCTIONS:
                return_blocks.append(last_block)
            pass
        pass

    # If the bytecode comes from Python, then there is possibly an
    # advantage in treating a return in a block as an instruction
    # which flows to the next instruction, since that will treat
    # blocks with unreachable instructions the way Python source
    # does - the code after that exists.
    #
    # However if you care about analysis, then
    # Hook RETURN_VALUE instructions to the exit block offset
    if more_precise_returns:
        for block in return_blocks:
            block.jump_offsets.add(end_bb_offset)
            block.edge_count += 1

    if len(BB.bb_list):
        BB.bb_list[-1].follow_offset = None
        BB.start_block = BB.bb_list[0]

    # Add remaining instructions?
    if start_offset <= end_offset:
        BB.bb_list.append(
            BasicBlock(
                start_offset,
                end_offset,
                loop_offset,
                None,
                flags=flags,
                jump_offsets=jump_offsets,
            )
        )
        loop_offset = None
        pass

    return BB


if __name__ == "__main__":
    offset2inst_index = {}
    bb_mgr = basic_blocks(basic_blocks, offset2inst_index)
    from pprint import pprint

    pprint(offset2inst_index)
    for bb in bb_mgr.bb_list:
        print(bb)

#!/usr/bin/env python
import opcode
import dis
from graph import (BB_BLOCK, BB_EXCEPT, BB_ENTRY,
                   BB_FINALLY, BB_FOR,
                   BB_JUMP_UNCONDITIONAL, BB_LOOP, BB_RETURN)

# We classify intructions into various categories (even though
# many of the below contain just one instruction). This can
# isolate us from instruction changes in Python.
# The classifications are used in setting basic block flag bits
BLOCK_INSTRUCTIONS   = set([opcode.opmap['POP_BLOCK']])
EXCEPT_INSTRUCTIONS  = set([opcode.opmap['POP_EXCEPT']])
FINALLY_INSTRUCTIONS = set([opcode.opmap['SETUP_FINALLY']])
FOR_INSTRUCTIONS     = set([opcode.opmap['FOR_ITER']])
JREL_INSTRUCTIONS    = set(opcode.hasjrel)
JABS_INSTRUCTIONS    = set(opcode.hasjabs)
JUMP_INSTRUCTIONS    = JABS_INSTRUCTIONS | JREL_INSTRUCTIONS
JUMP_UNCONDITONAL    = set([opcode.opmap['JUMP_ABSOLUTE'],
                            opcode.opmap['JUMP_FORWARD']])
LOOP_INSTRUCTIONS    = set([opcode.opmap['SETUP_LOOP'],
                            opcode.opmap['YIELD_VALUE'],
                           opcode.opmap['RAISE_VARARGS']])
RETURN_INSTRUCTIONS  = set([opcode.opmap['RETURN_VALUE'],
                            opcode.opmap['YIELD_VALUE'],
                            opcode.opmap['RAISE_VARARGS']])

class BasicBlock(object):
  """Represents a basic block from the bytecode. It's a bit more than
    just the a continuous range of the bytecode offsets. It also
    contains
      * jump-targets offsets,
      * flags that classify flow information in the block
      * graph node predcessor and successor sets, filled in a later phase
      * some layout information for dot graphing
  """

  def __init__(self, start_offset, end_offset, follow_offset,
               flags = set(),
               jump_offsets=set([])):

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

    # Jump offsets is the targets of all of the jump instructions
    # inside the basic block. Note that jump offsets can come from
    # things SETUP_.. operations as well as JUMP instructions
    self.jump_offsets = jump_offsets

    # flags is a set of interesting bits about the basic block.
    # Elements of the bits are BB_... constants
    self.flags = flags
    self.index = (start_offset, end_offset)

    # Lists of predecessor and successor bacic blocks
    # This is computed in cfg.
    self.predecessors = set([])
    self.successors = set([])

    # Set true if this is dead code, or unureachable
    self.unreachable = False


  # A nice print routine for a Basic block
  def __repr__(self):
      if len(self.jump_offsets) > 0:
        jump_text = ", jumps=%s" % sorted(self.jump_offsets)
      else:
        jump_text = ""
      if len(self.flags) > 0:
        flag_text = ", flags=%s" % sorted(self.flags)
      else:
        flag_text = ""
      return ('BasicBlock(range: %s%s, follow_offset=%s%s)'
              % (self.index, flag_text, self.follow_offset, jump_text))


def add_bb(bb_list, start_offset, end_offset, follow_offset, flags,
           jump_offsets):
  bb_list.append(BasicBlock(start_offset, end_offset,
                            follow_offset,
                            flags = flags,
                            jump_offsets = jump_offsets))
  start_offset = end_offset
  flags = set([])
  jump_offsets = set([])
  return flags, jump_offsets

def basic_blocks(co):
    """Create a list of basic blocks found in a code object
    """

    # Get jump targets
    jump_targets = set()
    for inst in dis.get_instructions(co):
        op = inst.opcode
        offset = inst.offset
        follow_offset = offset + 2 # Custom for 3.6
        if op in JUMP_INSTRUCTIONS:
            if op in JABS_INSTRUCTIONS:
                jump_offset = inst.arg
            else:
                jump_offset = follow_offset + inst.arg
            jump_targets.add(jump_offset)
            pass
        pass

    start_offset = 0
    end_offset = -1
    bb_list = []
    jump_offsets = set()
    prev_offset = -1
    flags = set([BB_ENTRY])

    for inst in dis.get_instructions(co):
        prev_offset = end_offset
        end_offset = inst.offset
        op = inst.opcode
        offset = inst.offset
        follow_offset = offset + 2 # Custom for 3.6

        if op in LOOP_INSTRUCTIONS:
            flags.add(BB_LOOP)

        if offset in jump_targets:
            # Fallthrough path and jump target path.
            # This instruction definitely starts a new basic block
            # Close off any prior basic block
            if start_offset < end_offset:
                flags, jump_offsets = add_bb(bb_list, start_offset,
                                               prev_offset, end_offset,
                                               flags, jump_offsets)
                start_offset = end_offset

        # Add block flags for certain classes of instructions
        if op in BLOCK_INSTRUCTIONS:
            flags.add(BB_BLOCK)
        elif op in EXCEPT_INSTRUCTIONS:
            flags.add(BB_EXCEPT)
        elif op in FINALLY_INSTRUCTIONS:
            flags.add(BB_FINALLY)
        elif op in FOR_INSTRUCTIONS:
            flags.add(BB_FOR)
        elif op in JUMP_INSTRUCTIONS:
            # Some sort of jump instruction.
            # While in theory an absolute jump could be part of the
            # same (extened) basic block, for our purposes we would like to
            # call them two basic blocks as that probably mirrors
            # the code more simply.

            # Figure out where we jump to amd add it to this
            # basic block's jump offsets.
            if op in JABS_INSTRUCTIONS:
                jump_offset = inst.arg
            else:
                jump_offset = follow_offset + inst.arg

            jump_offsets.add(jump_offset)
            if op in JUMP_UNCONDITONAL:
                flags.add(BB_JUMP_UNCONDITIONAL)
                flags, jump_offsets = add_bb(bb_list, start_offset,
                                               end_offset, follow_offset,
                                               flags, jump_offsets)
                start_offset = follow_offset
            else:
                flags, jump_offsets = add_bb(bb_list, start_offset,
                                               end_offset, follow_offset,
                                               flags, jump_offsets)
                start_offset = follow_offset

                pass
        elif op in RETURN_INSTRUCTIONS:
            flags.add(BB_RETURN)
            flags, jump_offsets = add_bb(bb_list, start_offset,
                                           end_offset, follow_offset,
                                           flags, jump_offsets)
            start_offset = follow_offset
            pass
        pass

    bb_list[-1].follow_offset = None
    if start_offset <= end_offset:
        bb_list.append(BasicBlock(start_offset, end_offset, None,
                                  flags=flags, jump_offsets=jump_offsets))

    return bb_list

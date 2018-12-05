#!/usr/bin/env python
from xdis import PYTHON_VERSION, PYTHON3, next_offset
from xdis.std import get_instructions
from control_flow.graph import (BB_POP_BLOCK, BB_SINGLE_POP_BLOCK, BB_STARTS_POP_BLOCK,
                                BB_EXCEPT, BB_ENTRY, BB_TRY, BB_EXIT,
                                BB_FINALLY, BB_END_FINALLY, BB_FOR, BB_BREAK,
                                BB_JUMP_CONDITIONAL, BB_JUMP_UNCONDITIONAL,
                                BB_LOOP, BB_NOFOLLOW)

# The byte code versions we support
PYTHON_VERSIONS = (# 1.5,
                   # 2.1, 2.2, 2.3, 2.4, 2.5, 2.6,
                   2.6, 2.7,
                   # 3.0, 3.1, 3.2, 3.3, 3.4
                   3.5, 3.6, 3.7)

end_bb = -1

class BasicBlock(object):
  """Basic block from the bytecode.

     It's a bit more than just the a continuous range of the bytecode offsets.

     It also contains:
       * jump-targets offsets,
       * exception-targets offsets,
       * flags that classify flow information in the block,
       * a graph node,
       * predecessor and successor sets, filled in a later phase
       * some layout information for dot graphing
  """

  def __init__(self, start_offset, end_offset, follow_offset,
               loop_offset,
               flags = set(),
               jump_offsets=set()):

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
    self.doms = set()

    # Set true if this is dead code, or unreachable
    self.unreachable = False
    self.number = end_bb
    self.edge_count = len(jump_offsets)
    if (follow_offset is not None and not
        BB_NOFOLLOW in self.flags):
      self.edge_count += 1

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
      return ('BasicBlock(#%d range: %s%s, follow_offset=%s, edge_count=%d%s%s)'
              % (self.number, self.index, flag_text, self.follow_offset,
                 self.edge_count, jump_text, exception_text))


class BBMgr(object):

  def __init__(self, version, is_pypy):
    global end_bb
    end_bb = 0
    self.bb_list = []
    self.exit_block = None

    # Pick up appropriate version
    if version in PYTHON_VERSIONS:
      if PYTHON3:
        if PYTHON_VERSION in (3.5, 3.6, 3.7):
          if PYTHON_VERSION == 3.5:
            import xdis.opcodes.opcode_35 as opcode
          elif PYTHON_VERSION == 3.6:
            import xdis.opcodes.opcode_36 as opcode
          else:
            import xdis.opcodes.opcode_37 as opcode
          self.opcode = opcode
          # We classify intructions into various categories (even though
          # many of the below contain just one instruction). This can
          # isolate us from instruction changes in Python.
          # The classifications are used in setting basic block flag bits
          self.POP_BLOCK_INSTRUCTIONS   = set([opcode.opmap['POP_BLOCK']])
          self.EXCEPT_INSTRUCTIONS      = set([opcode.opmap['POP_EXCEPT']])
          self.TRY_INSTRUCTIONS         = set([opcode.opmap['SETUP_EXCEPT']])
          self.END_FINALLY_INSTRUCTIONS = set([opcode.opmap['END_FINALLY']])
          self.FINALLY_INSTRUCTIONS     = set([opcode.opmap['SETUP_FINALLY']])
          self.FOR_INSTRUCTIONS         = set([opcode.opmap['FOR_ITER']])
          self.JREL_INSTRUCTIONS        = set(opcode.hasjrel)
          self.JABS_INSTRUCTIONS        = set(opcode.hasjabs)
          self.JUMP_INSTRUCTIONS        = self.JABS_INSTRUCTIONS | self.JREL_INSTRUCTIONS
          self.JUMP_UNCONDITONAL        = set([opcode.opmap['JUMP_ABSOLUTE'],
                                              opcode.opmap['JUMP_FORWARD']])
          self.JUMP_CONDITONAL          = set([opcode.opmap['POP_JUMP_IF_FALSE'],
                                               opcode.opmap['POP_JUMP_IF_TRUE'],
                                               opcode.opmap['JUMP_IF_FALSE_OR_POP'],
                                               opcode.opmap['JUMP_IF_TRUE_OR_POP']])

          self.LOOP_INSTRUCTIONS        = set([opcode.opmap['SETUP_LOOP']])
          # ??
          #                                   opcode.opmap['YIELD_VALUE'],
          #                                   opcode.opmap['RAISE_VARARGS']])
          self.BREAK_INSTRUCTIONS       = set([opcode.opmap['BREAK_LOOP']])
          self.NOFOLLOW_INSTRUCTIONS    = opcode.NOFOLLOW

      else:
        if PYTHON_VERSION in (2.6, 2.7):
          if PYTHON_VERSION == 2.7:
            import xdis.opcodes.opcode_27 as opcode
          else:
            import xdis.opcodes.opcode_26 as opcode
          self.opcode = opcode
          # We classify intructions into various categories (even though
          # many of the below contain just one instruction). This can
          # isolate us from instruction changes in Python.
          # The classifications are used in setting basic block flag bits
          self.POP_BLOCK_INSTRUCTIONS  = set([opcode.opmap['POP_BLOCK']])
          self.EXCEPT_INSTRUCTIONS     = set([])
          self.FINALLY_INSTRUCTIONS    = set([opcode.opmap['SETUP_FINALLY']])
          self.FOR_INSTRUCTIONS        = set([opcode.opmap['FOR_ITER']])
          self.JREL_INSTRUCTIONS       = set(opcode.hasjrel)
          self.JABS_INSTRUCTIONS       = set(opcode.hasjabs)
          self.JUMP_INSTRUCTIONS       = self.JABS_INSTRUCTIONS | self.JREL_INSTRUCTIONS
          self.JUMP_UNCONDITONAL       = set([opcode.opmap['JUMP_ABSOLUTE'],
                                             opcode.opmap['JUMP_FORWARD']])
          self.JUMP_CONDITONAL         = set([opcode.opmap['POP_JUMP_IF_FALSE'],
                                              opcode.opmap['POP_JUMP_IF_TRUE'],
                                              opcode.opmap['JUMP_IF_FALSE_OR_POP'],
                                              opcode.opmap['JUMP_IF_TRUE_OR_POP']])
          self.LOOP_INSTRUCTIONS       = set([opcode.opmap['SETUP_LOOP']]),
          # ??
          #                                   opcode.opmap['YIELD_VALUE'],
          #                                  opcode.opmap['RAISE_VARARGS']])
          self.BREAK_INSTRUCTIONS      = set([opcode.opmap['BREAK_LOOP']])
          self.NOFOLLOW_INSTRUCTIONS   = set([opcode.opmap['RETURN_VALUE'],
                                             opcode.opmap['YIELD_VALUE'],
                                             opcode.opmap['RAISE_VARARGS']])
    else:
      raise RuntimeError("Version %s not supported yet" % PYTHON_VERSION)

  def add_bb(self, start_offset, end_offset, loop_offset, follow_offset, flags,
             jump_offsets):

      if BB_STARTS_POP_BLOCK in flags and start_offset == end_offset:
          flags.remove(BB_STARTS_POP_BLOCK)
          flags.add(BB_SINGLE_POP_BLOCK)

      block = BasicBlock(start_offset, end_offset,
                        follow_offset,
                        flags = flags,
                        jump_offsets = jump_offsets,
                        loop_offset = loop_offset)
      self.bb_list.append(block)

      if BB_EXIT in flags:
          assert self.exit_block is None, "Should have only one exit"
          self.exit_block = block

      start_offset = end_offset
      flags = set([])
      jump_offsets = set([])
      return block, flags, jump_offsets


def basic_blocks(version, is_pypy, fn):
    """Create a list of basic blocks found in a code object
    """


    BB = BBMgr(version, is_pypy)

    # Get jump targets
    jump_targets = set()
    for inst in get_instructions(fn):
        op = inst.opcode
        offset = inst.offset
        follow_offset = next_offset(op, BB.opcode, offset)
        if op in BB.JUMP_INSTRUCTIONS:
            if op in BB.JABS_INSTRUCTIONS:
                jump_offset = inst.arg
            else:
                jump_offset = follow_offset + inst.arg
            jump_targets.add(jump_offset)
            pass

    start_offset = 0
    end_offset = -1
    jump_offsets = set()
    prev_offset = -1
    endloop_offsets = [-1]
    flags = set([BB_ENTRY])
    end_try_offset_stack = []
    try_stack = []
    end_try_offset = None
    loop_offset = None

    for inst in get_instructions(fn):
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
            block, flags, jump_offsets = BB.add_bb(start_offset, end_offset,
                                                   loop_offset, follow_offset,
                                                   flags, jump_offsets)
            loop_offset = None
            if BB_TRY in block.flags:
                try_stack.append(block)
            start_offset = follow_offset

        if offset in jump_targets:
            # Fallthrough path and jump target path.
            # This instruction definitely starts a new basic block
            # Close off any prior basic block
            if start_offset < end_offset:
                block, flags, jump_offsets = BB.add_bb(start_offset, prev_offset,
                                                       loop_offset, end_offset,
                                                       flags, jump_offsets)
                loop_offset = None
                if BB_TRY in block.flags:
                    try_stack.append(block)
                    pass

                start_offset = end_offset
                pass

        # Add block flags for certain classes of instructions
        if op in BB.JUMP_CONDITONAL:
            flags.add(BB_JUMP_CONDITIONAL)

        if op in BB.POP_BLOCK_INSTRUCTIONS:
            flags.add(BB_POP_BLOCK)
            if start_offset == offset:
                flags.add(BB_STARTS_POP_BLOCK)
                flags.remove(BB_POP_BLOCK)
        elif op in BB.EXCEPT_INSTRUCTIONS:
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
            block, flags, jump_offsets = BB.add_bb(start_offset, end_offset,
                                                   loop_offset, follow_offset,
                                                   flags, jump_offsets)
            loop_offset = None
            start_offset = follow_offset
        elif op in BB.JUMP_INSTRUCTIONS:
            # Some sort of jump instruction.
            # Figure out where we jump to amd add it to this
            # basic block's jump offsets.
            if op in BB.JABS_INSTRUCTIONS:
                jump_offset = inst.arg
            else:
                jump_offset = inst.argval

            jump_offsets.add(jump_offset)
            if op in BB.JUMP_UNCONDITONAL:
                flags.add(BB_JUMP_UNCONDITIONAL)
                block, flags, jump_offsets = BB.add_bb(start_offset, end_offset,
                                                       loop_offset, follow_offset,
                                                       flags, jump_offsets)
                loop_offset = None
                if BB_TRY in block.flags:
                    try_stack.append(block)
                    pass

                start_offset = follow_offset
            elif op != BB.opcode.SETUP_LOOP:
                if op in BB.FINALLY_INSTRUCTIONS:
                    flags.add(BB_FINALLY)

                block, flags, jump_offsets = BB.add_bb(start_offset, end_offset,
                                                       loop_offset, follow_offset,
                                                       flags, jump_offsets)
                loop_offset = None
                if BB_TRY in block.flags:
                    try_stack.append(block)
                start_offset = follow_offset

                pass
        elif op in BB.NOFOLLOW_INSTRUCTIONS:
            flags.add(BB_NOFOLLOW)
            last_block, flags, jump_offsets = BB.add_bb(start_offset, end_offset,
                                                        loop_offset, follow_offset,
                                                        flags, jump_offsets)
            loop_offset = None
            start_offset = follow_offset
            pass
        pass

    if len(BB.bb_list):
      BB.bb_list[-1].follow_offset = None
      BB.start_block = BB.bb_list[0]

    # Add remaining instructions?
    if start_offset <= end_offset:
        BB.bb_list.append(BasicBlock(start_offset, end_offset, loop_offset, None,
                                     flags=flags, jump_offsets=jump_offsets))
        loop_offset = None
        pass

    # Add an artificial block where we can link the exits of other blocks
    # to. This helps in computing reverse dominators.
    BB.add_bb(end_offset+1, end_offset+1, None, None, set([BB_EXIT]), [])
    return BB

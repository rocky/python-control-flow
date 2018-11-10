"""
From Basic Block control flow graph, create a
structured control flow graph.

This code is ugly.
"""
from xdis.std import get_instructions
from control_flow.graph import (BB_EXCEPT, BB_FINALLY, BB_FOR,
                                BB_LOOP, BB_NOFOLLOW, BB_STARTS_POP_BLOCK)

seen_blocks = set()

class ControlStructure(object):
  """Represents a basic block (or rather extended basic block) from the
    bytecode. It's a bit more than just the a continuous range of the
    bytecode offsets. It also contains * jump-targets offsets, * flags
    that classify flow information in the block * graph node
    predecessor and successor sets, filled in a later phase * some
    layout information for dot graphing

  """
  def __init__(self, block, kind, children):
      self.block = block
      self.kind = kind
      self.children = children

class LoopControlStructure(ControlStructure):
  def __init__(self, block, children):
      super(LoopControlStructure, self).__init__(block, 'loop', children)

class SequenceControlStructure(ControlStructure):
  def __init__(self, block, children):
      super(SequenceControlStructure, self).__init__(block, 'sequence', children)

class IfControlStructure(ControlStructure):
  def __init__(self, block, children):
      super(IfControlStructure, self).__init__(block, 'if', children)

class ThenControlStructure(ControlStructure):
  def __init__(self, block, then_children):
      super(ThenControlStructure, self).__init__(block, 'then', then_children)

class ElseControlStructure(ControlStructure):
  def __init__(self, block, else_children):
      super(ElseControlStructure, self).__init__(block, 'else', else_children)

class PopBlockStructure(ControlStructure):
  def __init__(self, block):
      super(PopBlockStructure, self).__init__(block, 'pop block', [])

class NoFollowControlStructure(ControlStructure):
  def __init__(self, block):
      super(NoFollowControlStructure, self).__init__(block, 'no follow', [])

class IfElseControlStructure(ControlStructure):
  def __init__(self, block, then_children, else_children):
      super(IfElseControlStructure, self).__init__(block, 'ifelse',
                                                   [then_children, else_children])

class ContinueControlStructure(ControlStructure):
  def __init__(self, block):
      super(ContinueControlStructure, self).__init__(block, 'continue', [])

# Don't know if we will do this here
class Elif(ControlStructure):
  def __init__(self, block, elif_children):
      super(LoopControlStructure, self).__init__(block, 'elif', [elif_children])

def build_control_structure(cfg, current):
    global seen_blocks
    seen_blocks = set()
    cs, follow  = control_structure_iter(cfg, cfg.entry_node)
    # FIXME: assert that seen_blocks in control_stucture_short should
    # be all of blocks (except dead code)
    if follow:
        cs.append(follow)
    # assert not set(cfg.blocks) - seen_blocks, "Some blocks not accounted for in structured cfg"
    return cs

def control_structure_iter(cfg, current, parent_kind='sequence'):
    result = []
    follow = []
    print("control_structure_iter: ", current)
    seen_blocks.add(current)
    block = cfg.blocks[current.number]

    # Traverse follow block
    if block.follow_offset is not None:
        follow_number = cfg.offset2block[block.follow_offset].bb.number
        follow_block = cfg.blocks[follow_number]
        is_loop = BB_LOOP in current.flags
        if is_loop:
            kind = 'loop'
        elif parent_kind == 'if':
            kind = 'then'
        elif parent_kind == 'else':
            kind = 'sequence'
        elif (parent_kind == 'sequence' and
              BB_STARTS_POP_BLOCK in block.flags):
            kind = 'sequence'
        # FIXME: the min(list) is funky because jump_offsets is a set
        elif block.jump_offsets and block.index[1] > min(list(block.jump_offsets)):
            kind = 'continue'
        else:
            # FIXME: add "try" and so on
            kind = 'if'

        dominator_blocks = {n.bb for n in block.dom_set}
        if BB_NOFOLLOW in current.flags or follow_block not in dominator_blocks:
            children = []
        else:
            children, follow  = control_structure_iter(cfg, follow_block, kind)

        if kind == 'loop':
            assert block.edge_count == 2
            if follow:
                children.append(follow)
            result.append(LoopControlStructure(block, children))
        elif kind == 'if':
            result.append(IfControlStructure(block, children))
            pass
        elif kind == 'then':
            result.append(ThenControlStructure(block, children))
        elif kind == 'continue':
            result.append(ContinueControlStructure(block))
        elif kind == 'sequence':
            pass
        pass

    # Traverse jump blocks, unless:
    #   we haven't already seen them; this happens in loop edges
    #   we do not dominate that block; here we defer to the encompassing dominator node
    for jump_offset in block.jump_offsets:
        jump_number = cfg.offset2block[jump_offset].bb.number
        jump_block = cfg.blocks[jump_number]
        # FIXME: may have to traverse in sequence, that is by dominator number or offset address?
        if jump_block in dominator_blocks and jump_block not in seen_blocks:
            if kind == 'if':
                if follow:
                    result.append(follow)
                    follow = []
                # Is this else  or not?
                if len(jump_block.predecessors) == 1:
                    if BB_STARTS_POP_BLOCK in jump_block.flags:
                        # this is outside of the "if"
                        assert jump_block.index[0] == jump_block.index[1]
                        result.append(PopBlockStructure(jump_block))
                    else:
                        # Although putting jump_block as the "else" clause
                        # of an "if" would not be incorrect, it is probably more common
                        # to have it follow the "then" block. That is:
                        #   if x:
                        #      return 5
                        #   return 6
                        # rathern than
                        #   if x:
                        #      return 5
                        #   else:
                        #      return 6
                        if BB_NOFOLLOW in jump_block.flags:
                            follow = NoFollowControlStructure(jump_block)
                        else:
                            jump_kind = 'else'
                            else_children, follow  = control_structure_iter(cfg, jump_block, jump_kind)
                            result[0].children.append(
                                ElseControlStructure(jump_block, else_children))
                            pass
                        pass
                    pass
                else:
                    assert len(jump_block.predecessors) != 0  # this would be dead code
                    jump_kind = 'sequence'
                    children, follow  = control_structure_iter(cfg, jump_block, jump_kind)
                    result[0].children.append(
                        SequenceControlStructure(jump_block, children))
            elif kind == 'continue':
                # Do nothing
                pass
            else:
                if kind not in ('then', 'else') or block.index[1] >= jump_offset:
                    # This is not quite right
                    jump_kind = 'sequence'
                    children, follow = control_structure_iter(cfg, jump_block, jump_kind)
                    if len(children) == 1:
                        result.append(children[0])
                    elif len(children) == 0:
                        pass
                    else:
                        result.append(SequenceControlStructure(jump_block, children))
                        pass
                else:
                    jump_kind = 'sequence'
                    follow, junk = control_structure_iter(cfg, jump_block, jump_kind)
                    assert not junk
                    pass
                pass
            pass
        pass
    return result, follow

def print_cs_tree(cs_list, indent=''):

    # FIXME: regularlize to list in generation?
    if not isinstance(cs_list, list):
        cs_list = [cs_list]

    for cs in cs_list:
        print("%s%s %s" % (indent, cs.kind, cs.block))
        for child in cs.children:
            if cs.kind != 'sequence':
                print_cs_tree(child, indent + '  ')
            else:
                print_cs_tree(child, indent)
            pass
        if cs.kind not in ('continue', 'pop block', 'no follow'):
          print("%send %s" % (indent, cs.kind))
    return

def print_structured_flow(fn, cfg, current):
    """Print structure skeleton"""
    print("\n" + ('-' * 40))
    bb_list = cfg.blocks

    offset2bb_start = {bb.start_offset: bb for bb in bb_list}
    offset2bb_end = {}
    setup_loop_target = set()
    for bb in bb_list:
        if not hasattr(bb, 'reach_offset'):
            # Dead code
            continue
        if bb.reach_offset not in offset2bb_end:
            print("reach_offset %d, bb #%d" % (bb.reach_offset, bb.number))
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
                if BB_LOOP in bb.flags:
                    print("[** loop dominator end for BB: #%s, start offset: %s, end offset: %d]" %
                          (bb.number, bb.index[0], bb.reach_offset))
                else:
                    print("** dominator end for BB: #%s, start offset: %s, end offset: %d" %
                          (bb.number, bb.index[0], bb.reach_offset))
                pass
            pass
        pass
    return

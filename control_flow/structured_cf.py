"""
From a control flow graph where the nodes are annotated basic blocks,
create a structured control flow graph.

This code is ugly.

"""
from __future__ import print_function
from xdis.std import get_instructions
from control_flow.graph import (BB_EXCEPT,
                                BB_FINALLY, BB_END_FINALLY,
                                BB_FOR,
                                BB_JUMP_CONDITIONAL, BB_JUMP_UNCONDITIONAL,
                                BB_LOOP, BB_NOFOLLOW, BB_TRY,
                                BB_SINGLE_POP_BLOCK,
                                BB_STARTS_POP_BLOCK)

class ControlStructure(object):
    """Encapsulates basic blocks in a way that is is nested and captures
    better the higher level structure better.

    While in concept we are mirroring the Python control structures like
    "if", "for", "for_else", "while", "while_else" it is not
    exactly the same, but it is kind of a hybrid between what is seen
    on the instruction level and what is seen at the Python source.

    Here are some examples that show the hybridization. We distingush
    block that start with "POP_BLOCK" and whether that block is a single
    instruction has more instructions. Tracking whether a block that
    starts "POP_BLOCK" is useful in detecting the end of a structures
    that add scope, and checking whether there is one or more
    instructions discriminates between constructs with "else" clauses
    like "while/for else".  Another example where there is a difference
    is that the instructoin that consists of the jump back to a loop is
    marked "continue" even though a Python "continue" instruction is
    generaly not explicitly coded at the end of a loop

    What we are mostly concerned with here is being able to insert
    instructions that an (Earley) parser can use to detect the right
    high-level control structure unambiguously.
    """

    def __init__(self, block, kind, children):
      self.block = block
      self.kind = kind
      self.children = children

class LoopControlStructure(ControlStructure):
    def __init__(self, block, children):
        super(LoopControlStructure, self).__init__(block, 'loop', children)
        return
    pass


class WhileControlStructure(ControlStructure):
    def __init__(self, block, children):
        super(WhileControlStructure, self).__init__(block, 'while', children)

class WhileElseControlStructure(ControlStructure):
    def __init__(self, block, children, else_children):
        super(WhileElseControlStructure, self).__init__(block, 'while_else', [children, else_children])

class ForControlStructure(ControlStructure):
    def __init__(self, block, children):
        super(ForControlStructure, self).__init__(block, 'for', children)

class ForElseControlStructure(ControlStructure):
    def __init__(self, block, children, else_children):
        super(ForElseControlStructure, self).__init__(block, 'for_else', [children, else_children])

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

class PopBlockSequenceStructure(ControlStructure):
    def __init__(self, block, children, kind):
        super(PopBlockSequenceStructure, self).__init__(block, kind, children)

class NoFollowControlStructure(ControlStructure):
    def __init__(self, block):
        super(NoFollowControlStructure, self).__init__(block, 'no follow', [])

class IfElseControlStructure(ControlStructure):
    def __init__(self, block, then_children, else_children):
        super(IfElseControlStructure, self).__init__(block, 'ifelse',
                                                   [then_children, else_children])
class TryControlStructure(ControlStructure):
    def __init__(self, block, try_block):
        super(TryControlStructure, self).__init__(block, 'try', try_block)

class TryElseControlStructure(ControlStructure):
    def __init__(self, block, children):
        super(TryElseControlStructure, self).__init__(block, 'try_else', children)
        return
    pass

class FinallyControlStructure(ControlStructure):
    def __init__(self, block, children):
        super(FinallyControlStructure, self).__init__(block, 'finally', children)

class EndFinallyControlStructure(ControlStructure):
    def __init__(self, block, finally_block):
        super(EndFinallyControlStructure, self).__init__(block, 'end_finally', [finally_block])

class ExceptControlStructure(ControlStructure):
    def __init__(self, block, except_children):
        super(ExceptControlStructure, self).__init__(block, 'except', except_children)

class ContinueControlStructure(ControlStructure):
    def __init__(self, block):
        super(ContinueControlStructure, self).__init__(block, 'continue', [])

# Don't know if we will do this here
class Elif(ControlStructure):
  def __init__(self, block, elif_children):
      super(LoopControlStructure, self).__init__(block, 'elif', [elif_children])

def build_control_structure(cfg, current):
    cfg.seen_blocks = set()
    cs, follow  = control_structure_iter(cfg, cfg.entry_node, None)
    # FIXME: assert that seen_blocks in control_stucture_short should
    # be all of blocks (except dead code)
    if follow:
        cs.append(follow)
    # assert not set(cfg.blocks) - seen_blocks, "Some blocks not accounted for in structured cfg"
    return cs

def loop_back(block):
    predecessors = block.predecessors
    start_offset = block.index[0]
    if len(predecessors) > 1:
        for p in predecessors:
            if p.index[0] > start_offset:
                return p
            pass
        pass
    return None

def predecessor_pop_block(cfg, block):
    """
    Does a predecessor of "block" a block that
    pops a block? We use this to distinguish
    in a loop to detect "while" and "while_else"
    constructs
    """
    for jump_offset in block.jump_offsets:
        jump_number = cfg.offset2block[jump_offset].bb.number
        jump_block = cfg.blocks[jump_number]
        if (BB_STARTS_POP_BLOCK in jump_block.flags or
            BB_SINGLE_POP_BLOCK in jump_block.flags):
            return jump_block
        pass
    return None


def control_structure_iter(cfg, current, parent, parent_kind='sequence'):
    print("control_structure_iter: ", current)

    result = []
    follow = []
    follow_block = None
    children = []

    cfg.seen_blocks.add(current)
    block = cfg.blocks[current.number]

    # Find follow block
    if block.follow_offset is not None:
        follow_number = cfg.offset2block[block.follow_offset].bb.number
        follow_block = cfg.blocks[follow_number]

    is_loop = BB_LOOP in current.flags
    ppb = predecessor_pop_block(cfg, block)
    starts_pop_block = BB_STARTS_POP_BLOCK in block.flags
    if is_loop:
        kind = 'loop'
    elif BB_TRY in current.flags:
        kind = 'try'
    elif BB_EXCEPT in current.flags:
        kind = 'except'
    elif BB_FINALLY in current.flags:
        kind = 'finally'
    elif BB_END_FINALLY in current.flags:
        kind = 'end_finally'
    elif parent_kind == 'if':
        children, follow = control_structure_iter(cfg, current, parent, 'sequence')
        kind = 'then'
    elif parent_kind == 'else':
        kind = 'sequence'
    elif (parent_kind in ('sequence', 'while_else', 'for_else') and starts_pop_block):
        kind = 'sequence pop block "%s"' % parent_kind
    elif (parent_kind in ('sequence', 'while', 'for') and
          BB_SINGLE_POP_BLOCK in block.flags):
        kind = 'pop block'
    elif (parent_kind == 'loop' and BB_FOR in block.flags):
        jump_offsets = list(block.jump_offsets)
        assert len(jump_offsets) == 1
        jump_offset = list(block.jump_offsets)[0]
        jump_number = cfg.offset2block[jump_offset].bb.number
        jump_block = cfg.blocks[jump_number]
        # For else blocks start with a POP_BLOCK and
        # do not end in an unconditional jump, but instead fall
        # through to the "for" end meet block.
        # if a: if ...then (for ... endfor) else ... endif
        # there will be a jump from the "for" around the "else"
        # as part of the "then" block. after the "for" is done.
        # Jut jump around the "else" will be POP_BLOCK, JUMP_ABSOLUTE.
        if (BB_STARTS_POP_BLOCK in jump_block.flags and
            BB_JUMP_UNCONDITIONAL not in jump_block.flags):
            kind = 'for_else'
        else:
            kind = 'for'
            pass
        pass
    # FIXME: the min(list) is funky because jump_offsets is a set
    elif block.jump_offsets and block.index[1] > min(list(block.jump_offsets)):
        kind = 'continue'
    elif (parent_kind == 'loop' and loop_back(block) and ppb):
        if BB_SINGLE_POP_BLOCK in ppb.flags:
            kind = 'while'
        else:
            assert BB_STARTS_POP_BLOCK in ppb.flags
            kind = 'while_else'
            pass
        pass
    elif (parent_kind == 'try' and
          current.start_offset in parent.jump_offsets):
        if parent in {node.bb for node in current.pdom_set}:
            kind = 'try meet'
        else:
            kind = 'try_else'
            pass
    elif BB_JUMP_CONDITIONAL in current.flags:
        kind = 'if'
    else:
        # FIXME: add others?
        kind = 'sequence'


    dominator_blocks = {n.bb for n in block.dom_set}
    if not children:
        if BB_NOFOLLOW in current.flags or follow_block not in dominator_blocks:
            children = []
        else:
            children, follow  = control_structure_iter(cfg, follow_block, current, kind)
            pass
        pass

    if kind == 'loop':
        assert block.edge_count == 2
        result.append(LoopControlStructure(block, children))
        if follow:
            children.append(follow)
            follow = []
            pass
    elif kind == 'while':
        result.append(WhileControlStructure(block, children))
        pass
    elif kind == 'for':
        result.append(ForControlStructure(block, children))
        pass
    elif kind == 'for_else':
        # else block is fixed up below.
        result.append(ForElseControlStructure(block, children, []))
        pass
    elif kind == 'try':
        for except_offset in block.exception_offsets | set(block.jump_offsets):
            except_number = cfg.offset2block[except_offset].bb.number
            except_block = cfg.blocks[except_number]
            if except_block not in cfg.seen_blocks:
                except_children, follow  = control_structure_iter(cfg, except_block, current, kind)
                children.append(except_children)
            pass
        result.append(TryControlStructure(block, children))
    elif kind == 'try_else':
        if follow:
            children.append(follow)
            pass
        result.append(TryElseControlStructure(block, children))
    elif kind == 'try meet':
        follow = SequenceControlStructure(block, children)
    elif kind == 'finally':
        result.append(FinallyControlStructure(block, children))
    elif kind == 'end_finally':
        # else block is fixed up below.
        if follow_block in {node.bb for node in current.dom_set}:
            end_finally_block = SequenceControlStructure(follow_block, [])
        else:
            end_finally_block = []
        result.append(EndFinallyControlStructure(block, end_finally_block))
    elif kind == 'except':
        result.append(ExceptControlStructure(block, children))
        pass
    elif kind == 'while_else':
        # else block is fixed up below.
        result.append(WhileElseControlStructure(block, children, []))
    elif kind == 'if':
        result.append(IfControlStructure(block, children))
        pass
    elif kind == 'then':
        if follow and current in {node.bb for node in parent.dom_set}:
            children.append(follow)
            follow = None
            pass
        result.append(ThenControlStructure(block, children))

    elif kind == 'continue':
        result.append(ContinueControlStructure(block))
    elif kind == 'pop block':
        result.append(PopBlockStructure(block))
    elif kind.startswith('sequence pop'):
        result.append(PopBlockSequenceStructure(block, children, kind))
    elif kind == 'sequence':
        result.append(SequenceControlStructure(block, children))
        pass
    pass

    # Traverse jump blocks, unless:
    #   we have already seen them; this happens in loop edges
    #   we do not dominate that block; here we defer to the encompassing dominator node
    for jump_offset in block.jump_offsets:
        jump_number = cfg.offset2block[jump_offset].bb.number
        jump_block = cfg.blocks[jump_number]
        # FIXME: may have to traverse in sequence, that is by dominator number or offset address?
        if jump_block in dominator_blocks and jump_block not in cfg.seen_blocks:
            if kind == 'if':
                if follow:
                    result.append(follow)
                    follow = []
                # Is this "if else"?
                if len(jump_block.predecessors) == 1:
                    if (BB_STARTS_POP_BLOCK in jump_block.flags or
                        BB_SINGLE_POP_BLOCK in jump_block.flags):
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
                            else_children, follow  = control_structure_iter(cfg, jump_block, current, jump_kind)
                            jump_dominator_blocks = {n.bb for n in jump_block.dom_set}
                            if follow and follow in jump_dominator_blocks:
                                follow = None
                                pass
                            result[0].children.append(
                                ElseControlStructure(jump_block, else_children))
                            pass
                        pass
                    pass
                else:
                    assert len(jump_block.predecessors) != 0  # this would be dead code
                    jump_kind = 'sequence'
                    children, follow  = control_structure_iter(cfg, jump_block, current, jump_kind)
                    if follow and jump_block.number != follow.block.number:
                        result[0].children.append(
                            SequenceControlStructure(jump_block, children))
                        pass
            elif kind in ('continue', 'try'):
                pass
                # Do nothing
            else:
                if kind not in ('then', 'else') or block.index[1] >= jump_offset:
                    # This is not quite right
                    jump_children, follow = control_structure_iter(cfg, jump_block, current, kind)
                    if kind in ['while_else', 'for_else']:
                        result[0].children[-1] = jump_children
                    elif len(jump_children) == 1:
                        result.append(jump_children[0])
                    elif len(jump_children) == 0 and kind != 'finally':
                        # FIXME: perhaps we *never* should do this?
                        pass
                    else:
                        result.append(SequenceControlStructure(jump_block, jump_children))
                        pass
                else:
                    jump_kind = 'sequence'
                    follow, junk = control_structure_iter(cfg, jump_block, current, jump_kind)
                    assert not junk
                    pass
                pass
            pass
        pass
    return result, follow

# FIXME: instead of or in additon to printing we need a structure
# that can be used in a revised print_structured_flow.
def cs_tree_to_str(cs_list, cs_marks, indent=''):

    # pop(0), insert(0,x)

    result = ''
    # FIXME: regularlize to pass in a list from the caller?
    if not isinstance(cs_list, list):
        cs_list = [cs_list]

    for cs in cs_list:
        result += "%s%s %s\n" % (indent, cs.kind, cs.block)
        if cs.kind in ('loop',
                       'while', 'while_else',
                       'for', 'for_else',
                       'else', 'then',
                       'try', 'try_else', 'except',
                       'sequence pop block "while_else"'):
            if cs.kind == 'loop':
                offset = cs.block.loop_offset
            else:
                offset = cs.block.start_offset
            offset_marks = cs_marks.get(offset, [])
            if cs.kind == 'sequence pop block "while_else"':
                cs.kind = 'WELSE_BLOCK'
            offset_marks.insert(0, cs.kind)
            cs_marks[offset] = offset_marks

        elif cs.kind in ('if', ):
            offset = cs.block.end_offset
            offset_marks = cs_marks.get(offset, [])
            offset_marks.insert(0, cs.kind)
            cs_marks[offset] = offset_marks


        for child in cs.children:
            if child and not cs.kind.startswith('sequence'):
                result += cs_tree_to_str(child, cs_marks, indent + '  ')
            else:
                result += cs_tree_to_str(child, cs_marks, indent)
                pass
            pass

        if ((cs.children and cs.block.start_offset != cs.block.end_offset)
            or cs.kind == 'for'):
            assert cs.block.start_offset <= cs.block.end_offset
            result += "%send %s\n" % (indent, cs.kind)
            pass
        pass
        if cs.kind in ('loop',
                       'while', 'while_else',
                       'for', 'for else',
                       'if', 'else', 'then',
                       'try', 'try_else', 'except',
                       'continue'):
            if cs.children:
                last_child = cs.children[-1] if cs.children[-1] else cs.children[0]
                while True:
                    if isinstance(last_child, list):
                        last_child = last_child[-1] if last_child[-1] else last_child[-2]
                    elif last_child.children:
                        if len(last_child.children) == 1 and not last_child.children[0]:
                            break
                        last_child = last_child.children
                    else:
                        break
                    pass
                end_offset = last_child.block.end_offset
            else:
                end_offset = cs.block.end_offset
            offset_marks = cs_marks.get(end_offset, [])
            offset_marks.append('end_' + cs.kind)
            cs_marks[end_offset] = offset_marks
    return result

# FIXME: this will be redone to use the result of cs_tree_to_str
def print_structured_flow(fn, cfg, current, cs_marks):
    """Print structure skeleton"""
    print("\n" + ('-' * 40))
    for inst in get_instructions(fn):
        offset = inst.offset
        remain = []
        if offset in cs_marks:
            for item in cs_marks[offset]:
                if not item.startswith('end'):
                    print(item.upper())
                else:
                    if item == 'end_continue':
                        item = 'CONTINUE'
                    remain.append(item)
                    pass
                pass
            pass
        print(inst.disassemble())
        for item in remain:
            print(item.upper())
            pass
        pass
    return

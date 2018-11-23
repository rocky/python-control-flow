from operator import attrgetter
from control_flow.dominators import DominatorTree
from control_flow.graph import (
  DiGraph, jump_flags, BB_LOOP, BB_NOFOLLOW, BB_TRY,
  BB_EXCEPT, BB_END_FINALLY)

class ControlFlowGraph(object):
  """
    Performs the control-flow analysis on set of basic blocks. It
    iterates over its bytecode and builds basic blocks with flag
    annotations. The final representation leverages the ``DiGraph``
    structure, and contains an instance of the ``DominatorTree``.
  """

  def __init__(self, blocks):
    self.seen_blocks = set()
    self.blocks = blocks
    self.offset2block = {}
    self.block_nodes = {}
    self.graph = None
    self.entry_node = None
    self.dom = None
    self.analyze(blocks)

  def dominators(self, blocks):
    """
      Returns the ``DominatorTree`` that contains:
       - Dominator tree (dict of IDom)
       - Dominance frontier (dict of CFG node -> set CFG nodes)
      This is lazily computed.
    """
    if self.dom is None:
        self.dom = DominatorTree(self)
    return self.dom

  def analyze(self, blocks):
      """
      Performs the Control-Flow Analysis and stores the resulting
      Control-Flow Graph.
      """
      self.entry = blocks[0]
      self.build_flowgraph(blocks)

  def build_flowgraph(self, blocks):
    g = DiGraph()

    self.block_offsets = {}
    self.block_nodes = {}

    # Add nodes
    for block in self.blocks:
      self.block_offsets[block.start_offset] = block
      block_node = g.make_add_node(block)
      self.block_nodes[block] = block_node
      self.offset2block[block.index[0]] = block_node

    # Compute a block's immediate predecessors and successors

    # In order to keep "try" blocks connected, if a block is an
    # "except" or "finally" block, we will treat the previous block as
    # though it falls into it. Even though it doesn't but should
    # instead end in a jump.
    prev_block = None
    for block in self.blocks:
      for jump_offset in block.jump_offsets:
          try:
              assert jump_offset in self.block_offsets
          except:
              from trepan.api import debug; debug()
          successor_block = self.block_offsets[jump_offset]
          successor_block.predecessors.add(block)
          block.successors.add(successor_block)
      if ( block.follow_offset
           and (not (jump_flags & block.flags or
                     (BB_NOFOLLOW in block.flags))) ):
        assert block.follow_offset in self.block_offsets
        successor_block = self.block_offsets[block.follow_offset]
        successor_block.predecessors.add(block)
        block.successors.add(successor_block)
        pass
      if (prev_block and
          (BB_TRY in prev_block.flags or
           BB_END_FINALLY in block.flags)):
        block.predecessors.add(prev_block)
        prev_block.successors.add(block)
      prev_block = block
      pass

    assert(len(self.blocks) > 0)
    self.entry_node = self.blocks[0]

    sorted_blocks = sorted(self.blocks, key=attrgetter('index'))
    for i, block in enumerate(sorted_blocks):

      # Is this this dead code? (Remove self loops in calculation)
      # Entry node, blocks[0] is never unreachable
      if not block.predecessors - set([block]) and block != blocks[0]:
        block.unreachable = True

      block = sorted_blocks[i]
      if block.follow_offset:
          if BB_NOFOLLOW in block.flags:
            kind = 'no fallthrough'
          else:
            kind = 'fallthrough'
          g.make_add_edge(
              self.block_nodes[block],
              self.block_nodes[self.block_offsets[block.follow_offset]],
              kind)
      # Connect the current block to its jump targets
      for jump_index in block.jump_offsets:
          target_block = self.block_offsets[jump_index]
          if jump_index > block.start_offset:
            if BB_LOOP in block.flags:
              edge_type = 'forward_scope'
            else:
              edge_type = 'forward'
          else:
            edge_type = 'backward'

          if self.block_nodes[target_block] == self.block_nodes[block]:
            edge_type = 'self-loop'

          g.make_add_edge(
              self.block_nodes[block],
              self.block_nodes[target_block],
              edge_type)
          pass
      for jump_index in block.exception_offsets:
          target_block = self.block_offsets[jump_index]
          try:
              assert jump_index >= block.start_offset
          except:
              from trepan.api import debug; debug()
          edge_type = 'exception'
          g.make_add_edge(
              self.block_nodes[block],
              self.block_nodes[target_block],
              edge_type)
          pass
      pass

    self.graph = g
    return

# Copyright (c) 2021, 2024 by Rocky Bernstein <rb@dustyfeet.com>
#
from operator import attrgetter
from typing import Dict, Optional, Tuple
from control_flow.graph import (
    DiGraph,
    Node,
    ScopeEdgeKind,
    TreeGraph,
    jump_flags,
    BB_JOIN_NODE,
    BB_JUMP_CONDITIONAL,
    BB_LOOP,
    BB_NOFOLLOW,
    BB_ENTRY,
    BB_EXIT,
)


class ControlFlowGraph:
    """
    Performs the control-flow analysis on set of basic blocks. It
    iterates over its bytecode and builds basic blocks with flag
    annotations. The final representation leverages the ``DiGraph``
    structure, and contains an instance of the ``DominatorTree``.
    """

    def __init__(self, bb_mgr):
        self.block_offsets = {}
        self.seen_blocks = set()
        self.blocks = bb_mgr.bb_list
        self.offset2block: Dict[int, Node] = {}
        self.offset2block_sorted: Tuple[int, Node] = tuple()
        self.block_nodes = {}
        self.graph = None
        self.entry_node = None
        self.exit_node = bb_mgr.exit_block

        #
        self.dom_tree = None
        # Maximum nesting in control flow graph. -1 means this hasn't been
        # computed. It is computed when self.dom_tree is computed and also is
        # stored in there.

        # Result from running dfs_forest.
        # FIXME: organize this better.
        self.dom_forest: Optional[TreeGraph] = None

        self.max_nesting_depth: int = -1

        self.analyze(self.blocks, bb_mgr.exit_block)

    def analyze(self, blocks, exit_block):
        """
        Performs the Control-Flow Analysis and stores the resulting
        Control-Flow Graph.
        """
        assert (
            len(blocks) >= 2
        ), "Should have at least a start block and an exception exit block"
        self.entry_node = blocks[1]
        self.build_flowgraph(blocks, exit_block)

    def build_flowgraph(self, blocks, exit_block):
        """
        Build a control-flow graph from basic blocks `blocks`.
        The exit block is `exit_block`.
        """
        g = DiGraph()

        self.block_nodes = {}

        # Add nodes
        exit_block = None
        offset2block = self.offset2block
        for block in self.blocks:
            self.block_offsets[block.start_offset] = block
            block_node = g.make_add_node(block)
            self.block_nodes[block] = block_node
            offset2block[block.index[0]] = block_node

            if BB_EXIT in block.flags:
                assert exit_block is None, f"Already saw exit block at: {exit_block}"
                exit_block = block
                self.exit_block = block_node
            pass

        # List of instruction offset to dominator information, sorted
        # by offset.  The only offsets here are the ones that start a
        # dominator region.  Sorting then is useful when to find out
        # dominator region an arbitrary offset lies in.
        self.offset2block_sorted = tuple(
            (offset, offset2block[offset]) for offset in sorted(offset2block.keys())
        )

        # Compute a block's immediate predecessors and successors

        for block in self.blocks:

            for jump_offset in set(block.jump_offsets) | block.exception_offsets:
                # We need to guard against jumps to wild offsets.
                # This was seen in
                # fontTools/ttLib/tables/ttProgram.cpython-310.pyc
                # line 359:
                #
                # 358        542 ...
                # 357        550 ...
                #            596 JUMP_FORWARD             5 (to 608)
                #        >>  598 POP_TOP
                #            600 EXTENDED_ARG           255
                #            602 EXTENDED_ARG         65535
                #            604 EXTENDED_ARG         16777215
                #            606 JUMP_FORWARD         4294967263 (to 8589935134)
                # 359    >>  608 ...
                #
                # The presumption is that some sort of optimization is
                # munging instructions above in code that is now dead.

                if jump_offset not in self.block_offsets:
                    continue
                successor_block = self.block_offsets[jump_offset]
                successor_block.predecessors.add(block)
                block.successors.add(successor_block)
            if BB_NOFOLLOW in block.flags:
                exit_block.predecessors.add(block)
                block.successors.add(exit_block)
                pass
            elif block.follow_offset and (not (jump_flags & block.flags)):
                assert block.follow_offset in self.block_offsets
                successor_block = self.block_offsets[block.follow_offset]
                successor_block.predecessors.add(block)
                block.successors.add(successor_block)
            pass

        assert (
            len(self.blocks) > 1
        ), "There should be at least a start and exception exit block"
        assert BB_ENTRY in self.blocks[1].flags, "We assume block 1 is the entry block"
        self.entry_node = self.blocks[1]

        sorted_blocks = sorted(self.blocks, key=attrgetter("index"))
        for i, block in enumerate(sorted_blocks):

            # Is this dead code? (Remove self loops in calculation)
            # Entry node, blocks[0] is never unreachable
            if not (block.predecessors - {block} and block != blocks[0]
                    or BB_ENTRY in block.flags):
                block.unreachable = True

            block = sorted_blocks[i]
            if block.follow_offset:
                if BB_NOFOLLOW in block.flags:
                    kind = "no fallthrough"
                    g.make_add_edge(
                        self.block_nodes[block], self.exit_block, "exit edge"
                    )
                else:
                    kind = "fallthrough"
                g.make_add_edge(
                    self.block_nodes[block],
                    self.block_nodes[self.block_offsets[block.follow_offset]],
                    kind,
                )
            elif BB_EXIT not in block.flags:
                g.make_add_edge(self.block_nodes[block], self.exit_block, "exit edge")

            # Connect the current block to its jump targets
            for jump_index in block.jump_offsets:
                # We need to guard against jumps to wild offsets. See
                # comment about this above.
                if jump_index in self.block_offsets:
                    target_block = self.block_offsets[jump_index]
                    if jump_index > block.start_offset:
                        if BB_LOOP in block.flags:
                            edge_kind = "for-finish"
                        elif BB_JUMP_CONDITIONAL in self.block_nodes[block].flags:
                            edge_kind = "forward-conditional"
                        else:
                            edge_kind = "forward"
                    else:
                        edge_kind = "looping"
                        pass

                    if self.block_nodes[target_block] == self.block_nodes[block]:
                        edge_kind = "self-loop"

                    g.make_add_edge(
                        self.block_nodes[block],
                        self.block_nodes[target_block],
                        edge_kind,
                    )
                    pass
                pass
            for jump_index in block.exception_offsets:
                source_block = self.block_offsets[jump_index]
                assert jump_index <= source_block.start_offset
                edge_kind = "exception"
                g.make_add_edge(
                    self.block_nodes[source_block], self.block_nodes[block], edge_kind
                )
                pass
            pass

        self.graph = g
        return

    def classify_edges(self):
        """
        Classify edges into alternate edges, looping edges, or join edges.
        There is a lower-level classification going on in edge.kind.
        """

        for edge in self.graph.edges:

            if edge.kind == "no fallthrough":
                # Edge is not to be followed.
                continue

            # If the immediate dominator of the source and destination
            # node is the same, then we have an alternate edge.
            # If the the edge is a backwards jump, then it is a looping edge
            # If the edge is not looping and the immediate dominator is
            # not the same, then we have a join edge.

            # Looping edges have already been classified, so use those when
            # we can.
            if edge.kind in ("backward", "self-loop"):
                edge.scoping_kind = ScopeEdgeKind.Looping
                continue
            source_block = edge.source.bb
            target_block = edge.dest.bb

            # print(f"Block #{source_block.number} -> Block #{target_block.number}")
            # if (source_block.number, target_block.number) == (2, 4):
            #     from trepan.api import debug; debug()

            if source_block.number == self.dom_tree.doms[target_block].number:
                # Jump to target starts a new scope.
                # Example:
                #   if <jump-to-then> then <jump-is-here> ... end
                edge.scoping_kind = ScopeEdgeKind.Alternate
            elif self.dom_tree.doms[source_block] == self.dom_tree.doms[target_block]:
                # if both source and target have the same immediate dominator, then
                # they are in the same scope and we have an alternation.
                # We eliminated the looping case above.
                edge.scoping_kind = ScopeEdgeKind.Alternate
            elif self.dom_tree.doms[source_block] > self.dom_tree.doms[target_block]:
                # The source block is jumping or falling out of a scope: its
                # `dom` or `scope number` is more nested than the target scope.
                # Examples:
                # "if ... <jump to end> else ... end" or
                # "if ... <falltrough after end> end" or
                # "while ... break <jump to end> ... end
                edge.scoping_kind = ScopeEdgeKind.Join
                target_block.flags.add(BB_JOIN_NODE)
            pass
        return

    def get_node(self, offset: int) -> Node:
        block = self.offset2block.get(offset, None)
        if block is not None:
            return block

        block = self.offset2block_sorted[0]

        # FIXME: use binary search
        for _, block in self.offset2block_sorted:
            if block.bb.start_offset <= offset <= block.bb.end_offset:
                break
            pass
        # Cache result computed
        self.offset2block[offset] = block
        return block

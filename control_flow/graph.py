# -*- coding: utf-8 -*-
"""
  Graph data structures

  Stripped down and modified from equip routine:
  :copyright: (c) 2018, 2021, 2023-2024 by Rocky Bernstein
  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
"""

from typing import Optional, Set
from enum import Enum

# First or Basic block that we entered on. Usually
# at offset 0.
# Does this need to be a set?
BB_ENTRY = 0

# Block is at the end, and doesn't have a following instruction.
# We have though an edge to the successor *instruction* for assisting displaying
# the control-flow graph the way the program was written.
BB_NOFOLLOW = 1

# a SETUP_LOOP instruction marking the beginning of a loop.
# the jump offset can indicate the range of the loop
BB_LOOP = 2

# A BREAK instruction breaking out of a loop
BB_BREAK = 3

# POP_BLOCKs detect presence of scope-defining
# blocks, and can be used to tell the difference between
# 'if's and 'whiles'
BB_POP_BLOCK = 4

# Does the basic block contain a single POP_BLOCK instruction?
# If so, it can signal the difference between "while else"
# and "while" (with no "else"). The latter has the single
# POP_BLOCK instruction.
BB_SINGLE_POP_BLOCK = 5

# Basic blocks that start out POP_BLOCK but have further
# instructions are generally in "else" clauses, like "while else"
BB_STARTS_POP_BLOCK = 6

BB_EXCEPT = 7

# Relative or absolute JUMP instructions. Occurs in "break", "continue",
# ends of loops, and in "if", "elif" constructs
BB_JUMP_UNCONDITIONAL = 8

# A FOR instruction which is an indicator of a "for" loop
BB_FOR = 9

# A "FINALLY" instruction which is an indicator of a "finally'
BB_FINALLY = 10

# A SETUP_EXCEPT is an indicator of "try"
BB_TRY = 11

# A "END_FINALLY" instruction which is the indicator of the *beginning*
# of a "finally' block
BB_END_FINALLY = 12

# An artificial block where all exits and returns are tied
# to. There will be only one such block, and it used in
# postdominsator or reverse dominiator calculation.
BB_EXIT = 13

# Has a conditional jump of some sort. This would be
# found in "if" constructs.
BB_JUMP_FORWARD_IF_FALSE = 14
BB_JUMP_FORWARD_IF_TRUE = 15
BB_JUMP_BACKWARD_IF_FALSE = 16
BB_JUMP_BACKWARD_IF_TRUE = 17

# Jumps to what would be the fallthough.
# If there were optimization, this instruction would be removed.
# This crud though can be useful in determining control
# structures that were used in the same way junk DNA may be
# useful in determining evolution history.

# We mostly use it in drawing graphs to make
# sure the jump arrow points straight down.
BB_JUMP_TO_FALLTHROUGH = 18

# The beginning of the basic block is a join.
BB_JOIN_POINT = 19

# Basic block ends in a return or an raise that is not inside
# a "try" block.
BB_RETURN = 20

# Unreachable block
BB_DEAD_CODE = 21

FLAG2NAME = {
    BB_ENTRY: "entry",
    BB_EXIT: "exit",
    BB_NOFOLLOW: "no fallthrough",
    BB_LOOP: "loop",
    BB_BREAK: "break",
    BB_POP_BLOCK: "block",
    BB_SINGLE_POP_BLOCK: "single pop block",
    BB_STARTS_POP_BLOCK: "starts with pop block",
    BB_EXCEPT: "except",
    BB_JOIN_POINT: "join block",
    BB_JUMP_UNCONDITIONAL: "unconditional",
    BB_JUMP_BACKWARD_IF_FALSE: "jump backward if false",
    BB_JUMP_BACKWARD_IF_TRUE: "jump backward if true",
    BB_JUMP_FORWARD_IF_FALSE: "jump forward if false",
    BB_JUMP_FORWARD_IF_TRUE: "jump forward if true",
    BB_JUMP_TO_FALLTHROUGH: "jump to fallthough",
    BB_FOR: "for",
    BB_FINALLY: "finally",
    BB_END_FINALLY: "end finally",
    BB_TRY: "try",
    BB_RETURN: "return",
}

# FIXME: some of the classifications may be overkill.
ScopeEdgeKind = Enum(
    "ScopeEdgeKind",
    [
        # Edge hasn't been computed yet:
        "Unknown",
        # Edge starts a new scope.
        # Example:
        #   if <jump-to-then> then <jump-is-here> ... end
        "NewScope",
        # Edge jumps from one alternate to the next one
        # Example:
        #   if <jump to elif test when condition not true> ... elif ... end
        "Alternate",
        # Edge joins from an inner scope to an outer one, e.g.
        # "if ... <jump to end> else ... end" or
        # "if ... <falltrough after end> end" or
        # "while ... break <jump to end> ... end
        "Join",
        # Edge jumps to a loop head
        "Looping",
    ],
)

jump_flags = set([BB_JUMP_UNCONDITIONAL, BB_BREAK])


def format_flags(flags):
    return ", ".join([FLAG2NAME[flag] for flag in FLAG2NAME if flag in flags])


def format_flags_with_width(flags, max_width, newline):
    result = ""
    r = 0
    sep = ""
    remain = max_width
    for flag in FLAG2NAME:
        if flag in flags:
            add = sep + FLAG2NAME[flag]
            a = len(add)
            remain = max_width - (r + a)
            if remain <= 1:
                if result:
                    result += "," + (" " * (remain - 1))
                    add = FLAG2NAME[flag]
                    pass
                result += newline
                r = 0
            r += a
            result += add
            sep = ", "
            pass
        pass

    return result + "}" + (" " * remain)


class Node:
    GLOBAL_COUNTER = 0

    def __init__(self, bb):
        Node.GLOBAL_COUNTER += 1
        if bb.number is None:
            self.number = Node.GLOBAL_COUNTER
        else:
            self.number = bb.number
        self.flags = bb.flags
        self.bb = bb

        # After the graph is built, a later pass
        # fills out the in edges and the out edges,
        # and whether the Node is a join Node.
        self.in_edges: Optional[Set[Node]] = None
        self.out_edges: Optional[Set[Node]] = None
        self.is_dead_code: Optional[bool] = None
        self.is_join_node: Optional[bool] = None

    @classmethod
    def reset(cls):
        cls.GLOBAL_COUNTER = 0

    def __eq__(self, obj) -> bool:
        return isinstance(obj, Node) and obj.number == self.number

    def __hash__(self) -> int:
        return hash("node-" + str(self.number))

    def __lt__(self, obj) -> bool:
        return not self.number < obj.number

    def __ne__(self, obj):
        return not self == obj

    def __repr__(self):

        return "Node%d(flags=%s, bb=%s)" % (
            self.number,
            repr(self.flags),
            repr(self.bb),
        )

    def __str__(self):
        return "Node%d(flags=%s, bb=%s)" % (
            self.number,
            repr(self.flags),
            str(self.bb),
        )


class Edge:
    GLOBAL_COUNTER = 0

    def __init__(self, source, dest, kind, data):
        Edge.GLOBAL_COUNTER += 1
        self.id = Edge.GLOBAL_COUNTER
        self.source = source
        self.dest = dest
        self.kind = kind
        self.scoping_kind = ScopeEdgeKind.Unknown
        self.flags = set()
        self.data = data

    @classmethod
    def reset(self):
        self.GLOBAL_COUNTER = 0

    def __ne__(self, obj):
        return not self == obj

    def __eq__(self, obj):
        return isinstance(obj, Edge) and obj.id == self.id

    def __hash__(self):
        return hash("edge-" + str(self.id))

    def __str__(self):
        return "Edge%d(source=%s, dest=%s, kind=%s, data=%s)" % (
            self.id,
            self.source,
            self.dest,
            str(self.kind),
            str(self.data),
        )

    def __repr__(self):
        return "Edge%d(source=%s, dest=%s, kind=%s, data=%s)" % (
            self.id,
            self.source,
            self.dest,
            repr(self.kind),
            repr(self.data),
        )

    def is_conditional_jump(self) -> bool:
        """Return True is edge is attached to a conditional jump
        instruction at its source.
        """
        return {
            BB_JUMP_FORWARD_IF_TRUE,
            BB_JUMP_FORWARD_IF_FALSE,
            BB_JUMP_BACKWARD_IF_TRUE,
            BB_JUMP_BACKWARD_IF_FALSE,
        }.intersection(
            self.source.flags
        ) and self.dest.bb.start_offset in self.source.bb.jump_offsets


class DiGraph:
    """
    A simple directed-graph structure.
    """

    def __init__(self):
        Node.reset()
        Edge.reset()
        self.nodes = set()
        self.edges = set()

        # Maximum nesting of graph. -1 means this hasn't been
        # computed.
        self.max_nesting: int = -1

    def add_edge(self, edge):
        if edge in self.edges:
            raise Exception("Edge already present")
        source_node, dest_node = edge.source, edge.dest

        self.edges.add(edge)
        self.add_node(source_node)
        self.add_node(dest_node)

    def add_node(self, node):
        self.nodes.add(node)

    def to_dot(self, exit_node, is_dominator_format: bool = False):
        from control_flow.dotio import DotConverter

        return DotConverter.process(self, exit_node, is_dominator_format)

    def add_edge_info_to_nodes(self):
        """
        Go through the graph and fill out `self.in_edges` and `self.out_edges`.
        """
        for node in self.nodes:
            node.out_edges = set()
            node.in_edges = set()

        for edge in self.edges:
            edge.source.out_edges.add(edge)
            edge.dest.in_edges.add(edge)

    @staticmethod
    def make_node(bb):
        return Node(bb)

    @staticmethod
    def make_edge(source=None, dest=None, kind=None, data=None):
        return Edge(source=source, dest=dest, kind=kind, data=data)

    # Some helpers
    def make_add_node(self, bb):
        node = DiGraph.make_node(bb)
        self.add_node(node)
        return node

    def make_add_edge(self, source=None, dest=None, kind=None, data=None) -> Edge:
        edge = DiGraph.make_edge(source=source, dest=dest, kind=kind, data=data)
        self.add_edge(edge)
        return edge


class TreeGraph(DiGraph):
    """
    A simple tree structure for basic blocks.
    """

    def __init__(self, root):
        Edge.reset()
        Node.reset()
        self.edges = set()
        self.nodes = []
        self.root = root
        self.root_node = None

        # Maximum nesting of graph. -1 means this hasn't been
        # computed.
        self.max_nesting: int = -1

    def add_edge(self, edge):
        if edge in self.edges:
            raise Exception("Edge already present")
        source_node, dest_node = edge.source, edge.dest

        self.add_node(source_node)
        self.add_node(dest_node)
        self.edges.add(edge)
        source_node.children |= set([dest_node])
        dest_node.parent = set([source_node])

    def add_node(self, node):
        if node.bb not in [n.bb for n in self.nodes]:
            node.children = set([])
            node.parent = None
            self.nodes.append(node)

    def postorder_traverse(self):
        """Traverse the tree in preorder"""
        if self.nodes:
            return self.postorder_traverse1(self.nodes[0])

    def postorder_traverse1(self, node):
        """Traverse the tree in preorder"""
        for child in node.children:
            self.postorder_traverse1(child)
            yield child
        yield node


def write_dot(
    name: str,
    prefix: str,
    graph: Optional[DiGraph],
    write_png: bool = False,
    debug=True,
    is_dominator_format: bool = False,
    exit_node=None,
):
    """Produce and write dot and png files for control-flow graph
    `cfg`; `func_or_code_name` is the func_or_code_name of the
    code and `prefix` indicates the file prefix to use.
    dot is converted to PNG and dumped if `write_bool` is True.
    """

    if graph is None:
        return

    path_safe = name.translate(name.maketrans(" <>", "_[]"))
    dot_path = f"{prefix}-{path_safe}.dot"
    open(dot_path, "w").write(graph.to_dot(exit_node, is_dominator_format))
    if debug:
        print(f"{dot_path} written")
    if write_png:
        import os

        png_path = f"{prefix}-{path_safe}.png"
        os.system(f"dot -Tpng {dot_path} > {png_path}")
        if debug:
            print(f"{png_path} written")

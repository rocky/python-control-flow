# -*- coding: utf-8 -*-
"""
  Graph data structures

  Stripped down and modified from equip routine:
  :copyright: (c) 2018, 2021, 2023 by Rocky Bernstein
  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
"""

# First or Basic block that we entered on. Usually
# at offset 0.
# Does this need to be a set?
BB_ENTRY = 0

# Block is at the end and doesn't have a following instruction.
BB_NOFOLLOW = 1

# a SETUP_LOOP instruction marking the beginning of a loop.
# the jump offset can indicate the range of the loop
BB_LOOP = 2

# A BREAK instruction breaking out of a loop
BB_BREAK = 3

# POP_BLOCKs detect presense of scope-defining
# blocks, and can be used to tell the diffrence between
# 'if's and 'whiles'
BB_POP_BLOCK = 4

# Does the basic block contain a single POP_BLOCK instruction?
# If so, it can signle the difference between "while else"
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

# An artifical block where all exits and returns are tied
# to. There will be only one such block, and it used in
# postdominsator or reverse dominiator calculation.
BB_EXIT = 13

# Has a conditional jump of some sort. This would be
# found in "if", and "while" constructs.
BB_JUMP_CONDITIONAL = 14

# Jumps to what would be the fallthough.
# If there were optimization, this instruction would be removed.
# This crud though can be useful in determining control
# structures that were used in the same way junk DNA may be
# useful in determining evolution history.

# We mostly use it in drawing graphs to make
# sure the jump arrow points straight down.
BB_JUMP_TO_FALLTHROUGH = 15

# Basic block ends in a return or an raise that is not inside
# a "try" block.
BB_RETURN = 16

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
    BB_JUMP_UNCONDITIONAL: "unconditional",
    BB_JUMP_CONDITIONAL: "conditional jump",
    BB_JUMP_TO_FALLTHROUGH: "jump to fallthough",
    BB_FOR: "for",
    BB_FINALLY: "finally",
    BB_END_FINALLY: "end finally",
    BB_TRY: "try",
    BB_RETURN: "return",
}


jump_flags = set([BB_JUMP_UNCONDITIONAL, BB_BREAK])
nofollow_flags = set([BB_NOFOLLOW])


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

    return result + (" " * remain)


class Node(object):
    GLOBAL_COUNTER = 0

    def __init__(self, bb):
        Node.GLOBAL_COUNTER += 1
        if bb.number is None:
            self.number = Node.GLOBAL_COUNTER
        else:
            self.number = bb.number
        self.flags = bb.flags
        self.bb = bb

    @classmethod
    def reset(self):
        self.GLOBAL_COUNTER = 0

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


class Edge(object):
    GLOBAL_COUNTER = 0

    def __init__(self, source, dest, kind, data):
        Edge.GLOBAL_COUNTER += 1
        self.id = Edge.GLOBAL_COUNTER
        self.source = source
        self.dest = dest
        self.kind = kind
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

    def __repr__(self):
        return "Edge%d(source=%s, dest=%s, kind=%s, data=%s)" % (
            self.id,
            self.source,
            self.dest,
            repr(self.kind),
            repr(self.data),
        )


class DiGraph(object):
    """
    A simple directed-graph structure.
    """

    def __init__(self):
        Node.reset()
        Edge.reset()
        self.nodes = set()
        self.edges = set()

    def add_edge(self, edge):
        if edge in self.edges:
            raise Exception("Edge already present")
        source_node, dest_node = edge.source, edge.dest

        self.edges.add(edge)
        self.add_node(source_node)
        self.add_node(dest_node)

    def add_node(self, node):
        self.nodes.add(node)

    def to_dot(self, show_exit=False):
        from control_flow.dotio import DotConverter

        return DotConverter.process(self, show_exit)

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

    def make_add_edge(self, source=None, dest=None, kind=None, data=None):
        edge = DiGraph.make_edge(source=source, dest=dest, kind=kind, data=data)
        self.add_edge(edge)
        return edge


class TreeGraph(DiGraph):
    """
    A simple tree structure for basic blocks.
    """

    def __init__(self, root):
        Node.reset()
        Edge.reset()
        self.root = root
        self.nodes = []
        self.edges = set()

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

def write_dot(name: str, prefix: str, graph, write_png: bool = False, debug=True):
    """Produce and write dot and png files for control-flow graph `cfg`;
    `func_or_code_name` is the func_or_code_name of the code and `prefix` indicates the
    file prefix to use.

      dot is converted to PNG and dumped if `write_bool` is True.
    """
    path_safe = name.translate(name.maketrans(" <>", "_[]"))
    dot_path = f"{prefix}{path_safe}.dot"
    open(dot_path, "w").write(graph.to_dot(False))
    if debug:
        print(f"{dot_path} written")
    if write_png:
        import os

        png_path = f"{prefix}{path_safe}.png"
        os.system(f"dot -Tpng {dot_path} > {png_path}")
        if debug:
            print(f"{png_path} written")

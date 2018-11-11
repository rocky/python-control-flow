# -*- coding: utf-8 -*-
"""
  Graph data structures

  Stripped down and modified from equip routine:
  :copyright: (c) 2018 by Rocky Bernstein
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

FLAG2NAME = {
  BB_ENTRY:              'entry',
  BB_NOFOLLOW:           'no fallthrough',
  BB_LOOP:               'loop',
  BB_BREAK:              'break',
  BB_POP_BLOCK:          'block',
  BB_SINGLE_POP_BLOCK:   'single pop block',
  BB_STARTS_POP_BLOCK:   'starts with pop block',
  BB_EXCEPT:             'except',
  BB_JUMP_UNCONDITIONAL: 'unconditional',
  BB_FOR:                'for',
  BB_FINALLY:            'finally',
}


jump_flags = set([BB_JUMP_UNCONDITIONAL, BB_BREAK])
nofollow_flags = set([BB_NOFOLLOW])

def format_flags(flags):
    return ', '.join([FLAG2NAME[flag] for flag in FLAG2NAME if flag in flags])

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

    def __ne__(self, obj):
        return not self == obj

    def __eq__(self, obj):
        return isinstance(obj, Node) and obj.number == self.number

    def __hash__(self):
        return hash('node-' + str(self.number))

    def __repr__(self):
        return 'Node%d(flags=%s, bb=%s)' % (self.number, repr(self.flags), repr(self.bb))


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
        return hash('edge-' + str(self.id))

    def __repr__(self):
        return 'Edge%d(source=%s, dest=%s, kind=%s, data=%s)' \
               % (self.id, self.source, self.dest, repr(self.kind), repr(self.data))


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
          raise Exception('Edge already present')
        source_node, dest_node = edge.source, edge.dest

        self.edges.add(edge)
        self.add_node(source_node)
        self.add_node(dest_node)

    def add_node(self, node):
        self.nodes.add(node)

    def to_dot(self):
        from control_flow.dotio import DotConverter
        return DotConverter.process(self)

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

    def __init__(self):
        Node.reset()
        Edge.reset()
        self.nodes = []
        self.edges = set()


    def add_edge(self, edge):
        if edge in self.edges:
            raise Exception('Edge already present')
        source_node, dest_node = edge.source, edge.dest

        self.add_node(source_node)
        self.add_node(dest_node)
        self.edges.add(edge)
        source_node.children |= set([dest_node])
        dest_node.parent = set([source_node])

    def add_node(self, node):
        if not node.bb in [n.bb for n in self.nodes]:
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

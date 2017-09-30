# -*- coding: utf-8 -*-
"""
  Graph data structures

  Stripped down and modified from equip routine:
  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
"""

# Does this need to be a set?
BB_ENTRY = 0
BB_NOFOLLOW = 1
BB_LOOP = 2
BB_BREAK = 3
BB_BLOCK = 4
BB_EXCEPT = 5
BB_JUMP_UNCONDITIONAL = 6
BB_FOR = 7
BB_FINALLY = 8


FLAG2NAME = {
  BB_ENTRY: 'entry',
  BB_NOFOLLOW: 'no fallthrough',
  BB_LOOP: 'loop',
  BB_BREAK: 'break',
  BB_BLOCK:'block',
  BB_EXCEPT: 'except',
  BB_JUMP_UNCONDITIONAL: 'unconditional',
  BB_FOR: 'for',
  BB_FINALLY: 'finally',
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
        bb.number = Node.GLOBAL_COUNTER

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
        from dotio import DotConverter
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
            self.nodes.add(node)

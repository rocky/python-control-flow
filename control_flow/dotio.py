# -*- coding: utf-8 -*-
"""
  Converts graph to dot format

  :copyright: (c) 2018 by Rocky Bernstein
  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
"""

from control_flow.graph import (
  DiGraph, BB_ENTRY, BB_NOFOLLOW, BB_JUMP_UNCONDITIONAL, format_flags)

DOT_STYLE = """
rankdir=TD; ordering=out;
graph[fontsize=10 fontname="Verdana"];
color="#efefef";
node[shape=box style=filled fontsize=8 fontname="Verdana" fillcolor="#efefef"];
edge[fontsize=8 fontname="Verdana"];
"""

class DotConverter(object):
  def __init__(self, graph):
    self.g = graph
    self.buffer = ''
    self.node_ids = {}

  @staticmethod
  def process(graph):
    converter = DotConverter(graph)
    converter.run()
    return converter.buffer

  def run(self):
    self.buffer += 'digraph G {'
    self.buffer += DOT_STYLE

    if isinstance(self.g, DiGraph):
      for node in sorted(self.g.nodes, key=lambda n: n.number):
        self.node_ids[node] = 'node_%d' % node.number
        self.add_node(node)

      for edge in self.g.edges:
        self.add_edge(edge)

    self.buffer += '}\n'


  def add_edge(self, edge):
    # labels = ''
    # if edge.flags is not None:
    #   bb = '' if edge.bb is None else str(edge.bb)
    #   labels = '[label="%s - %s"]' % (edge.flags, bb)

    # color="black:invis:black"]

    style = ''
    edge_port = ''
    if edge.kind in ('fallthrough', 'follow', 'dom-edge'):
        if edge.kind == 'follow':
          style = '[style="invis"]'
        weight = 10
    elif edge.kind == 'exception':
        style = '[color="red"]'
        weight = 1
    else:
      if edge.kind == 'forward_scope':
        style = '[style="dotted"]'
      if edge.kind == 'self-loop':
        edge_port = '[headport=ne] [tailport=se]';
      weight = 1

    if BB_NOFOLLOW in edge.source.flags:
      style = '[style="dashed"] [arrowhead="none"]'
      weight = 10

    if style == '' and edge.source.bb.unreachable:
      style = '[style="dashed"] [arrowhead="empty"]'

    if edge.dest.bb.unreachable:
      style = '[style="dashed"] [arrowhead="empty"]'

    if (edge.kind == 'fallthrough' and
        BB_JUMP_UNCONDITIONAL in edge.source.flags):
      # style = '[color="black:invis:black"]'
       style = '[style="dotted"] [arrowhead="empty"]'

    nid1 = self.node_ids[edge.source]
    nid2 = self.node_ids[edge.dest]

    self.buffer += ('%s -> %s [weight=%d]%s%s;\n' %
                    (nid1, nid2, weight, style, edge_port))

  @staticmethod
  def node_repr(node):
      if len(node.jump_offsets) > 0:
        jump_text = "\ljumps=%s" % sorted(node.jump_offsets)
      else:
        jump_text = ""
      if node.flags:
        flag_text = "\lflags=%s" % format_flags(node.flags)
      else:
        flag_text = ""

      if hasattr(node, 'reach_offset'):
        reach_offset_text = "\lreach_offset=%d" % node.reach_offset
      else:
        reach_offset_text = ""

      return ('offsets: %d..%d%s%s%s'
            % (node.start_offset, node.end_offset,
               flag_text, jump_text, reach_offset_text))


  def add_node(self, node):
    label = ''
    style = ''
    if BB_ENTRY in node.bb.flags:
      style = '[shape = "oval"]'
    elif not node.bb.predecessors:
      style = '[style = "dashed"]'
    label = '[label="Basic Block %d\l%s\l"]' % (node.number, self.node_repr(node.bb))
    self.buffer += 'node_%d %s%s;\n' % (node.number, style, label)

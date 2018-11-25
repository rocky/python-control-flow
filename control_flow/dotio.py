# -*- coding: utf-8 -*-
"""
  Converts graph to dot format

  :copyright: (c) 2018 by Rocky Bernstein
  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
"""

from control_flow.graph import (
    DiGraph, BB_ENTRY, BB_EXIT,
    BB_NOFOLLOW, BB_JUMP_UNCONDITIONAL, format_flags)

DOT_STYLE = """
  graph[fontsize=10 fontname="Verdana"];

  mclimit=1.5;
  rankdir=TD; ordering=out;
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
  def process(graph, show_exit):
      converter = DotConverter(graph)
      converter.run(show_exit)
      return converter.buffer

  def run(self, show_exit):
    self.buffer += 'digraph G {'
    self.buffer += DOT_STYLE

    if isinstance(self.g, DiGraph):
        self.buffer += "\n  # nodes:\n"
        for node in sorted(self.g.nodes, key=lambda n: n.number):
            self.node_ids[node] = 'node_%d' % node.number
            self.add_node(node, show_exit)

        self.buffer += "\n  # edges:\n"
        for edge in self.g.edges:
            self.add_edge(edge, show_exit)

    self.buffer += '}\n'


  def add_edge(self, edge, show_exit):
      # labels = ''
      # if edge.flags is not None:
      #   bb = '' if edge.bb is None else str(edge.bb)
      #   labels = '[label="%s - %s"]' % (edge.flags, bb)

      # color="black:invis:black"]

      if not show_exit and BB_EXIT in edge.dest.bb.flags:
          return

      style = ''
      edge_port = ''

      if edge.kind in ('fallthrough', 'no fallthrough',
                         'follow', 'exit edge', 'dom-edge'):
          if edge.kind == 'follow':
              style = '[style="invis"]'
              pass
          if edge.kind != 'exit edge':
              weight = 10
      elif edge.kind == 'exception':
          style = '[color="red"]'
          # edge_port = '[headport=nw] [tailport=sw]';
          # edge_port = '[headport=_] [tailport=_]';
          weight = 1
      else:
            if edge.kind == 'forward_scope':
                style = '[style="dotted"]'
                pass
            if edge.kind == 'self-loop':
                edge_port = '[headport=ne] [tailport=se]';
                pass
            weight = 1
            pass

      if BB_EXIT in edge.dest.flags:
            style = '[style="dotted"] [arrowhead="none"]'
            weight = 2
      elif BB_NOFOLLOW in edge.source.flags:
            style = '[style="dashed"] [arrowhead="none"]'
            weight = 10

      if style == '' and edge.source.bb.unreachable:
            style = '[style="dashed"] [arrowhead="empty"]'

      if edge.dest.bb.unreachable:
            style = '[style="dashed"] [arrowhead="empty"]'
            pass

      if (edge.kind == 'fallthrough' and
          BB_JUMP_UNCONDITIONAL in edge.source.flags):
          # style = '[color="black:invis:black"]'
          # style = '[style="dotted"] [arrowhead="empty"]'
          style = '[style="invis"]'

      nid1 = self.node_ids[edge.source]
      nid2 = self.node_ids[edge.dest]

      self.buffer += ('  %s -> %s [weight=%d]%s%s;\n' %
                        (nid1, nid2, weight, style, edge_port))

  @staticmethod
  def node_repr(node, align, is_exit):
      jump_text = ""
      if not is_exit and len(node.jump_offsets) > 0:
          jump_text = "\ljumps=%s" % sorted(node.jump_offsets)
          pass

      if node.flags:
          flag_text = "%sflags=%s" % (align, format_flags(node.flags))
      else:
          flag_text = ""
          pass

      if is_exit:
          return "flags=exit"

      reach_offset_text = ""
      if hasattr(node, 'reach_offset'):
        reach_offset_text = "\lreach_offset=%d" % node.reach_offset

      return ('offsets: %d..%d%s%s%s'
            % (node.start_offset, node.end_offset,
               flag_text, jump_text, reach_offset_text))


  def add_node(self, node, show_exit):

      if not show_exit and BB_EXIT in node.bb.flags:
          return

      label = ''
      style = ''
      align = '\l'

      is_exit = False
      if BB_ENTRY in node.bb.flags:
          style = '[shape = "oval"]'
      elif BB_EXIT in node.bb.flags:
          style = '[shape = "diamond"]'
          align = '\n'
          is_exit = True
      elif not node.bb.predecessors:
          style = '[style = "dashed"]'
          pass
      label = ('[label="Basic Block %d%s%s%s"]' %
               (node.number, align, self.node_repr(node.bb, align, is_exit),
                align))
      self.buffer += '  node_%d %s%s;\n' % (node.number, style, label)

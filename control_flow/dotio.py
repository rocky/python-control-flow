# -*- coding: utf-8 -*-
"""
  Converts graph to dot format

  :copyright: (c) 2018 by Rocky Bernstein
  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
"""

from control_flow.graph import (
    DiGraph, BB_ENTRY, BB_EXIT, BB_END_FINALLY,
    BB_NOFOLLOW, BB_JUMP_UNCONDITIONAL, format_flags_with_width)

DOT_STYLE = """
  graph[fontsize=10 fontname="DejaVu Sans Mono"];

  mclimit=1.5;
  rankdir=TD; ordering=out;
  color="#efefef";

  node[shape=box style=filled fontsize=10 fontname="DejaVu Sans Mono"
       fillcolor="#efefef", width=2];
  edge[fontsize=10 fontname="Verdana"];
"""

flags_prefix = "flags="
FEL = len(flags_prefix)
NODE_TEXT_WIDTH = 26 + FEL

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

  # See Stackoverflow link below for information on how imporve
  # layout of graph. It's a mess and not very well understood.
  def run(self, show_exit):
    self.buffer += 'digraph G {'
    self.buffer += DOT_STYLE

    if isinstance(self.g, DiGraph):
        self.buffer += "\n  # basic blocks:\n"
        for node in sorted(self.g.nodes, key=lambda n: n.number):
            self.node_ids[node] = 'block_%d' % node.number
            self.add_node(node, show_exit)

        self.buffer += """
  # Edges should be ordered from innermost block edges to outmost.
  # If layout gives ugly edge crossing, change the order or the edges
  # and/or add port directions on nodes For example:
  #  block_1:sw -> block_4:nw or
  #  block_0 -> block_3:ne
  # See https://stackoverflow.com/questions/53468814/how-can-i-influence-graphviz-dot-to-prefer-which-edges-can-cross/53472852#53472852

"""
        # FIXME: We really want in reverse dominiator order but I think this is
        # close approximation.
        seen_edge = set()
        for edge in sorted(self.g.edges, reverse=True,
                           key=lambda n: (n.source.number, -n.dest.number)):
            edge_pair  = (edge.source.number, edge.dest.number)
            self.add_edge(edge, show_exit, edge_pair in seen_edge)
            seen_edge.add(edge_pair)

    self.buffer += '}\n'


  def add_edge(self, edge, show_exit, edge_seen):
      # labels = ''
      # if edge.flags is not None:
      #   bb = '' if edge.bb is None else str(edge.bb)
      #   labels = '[label="%s - %s"]' % (edge.flags, bb)

      # color="black:invis:black"]

      if not show_exit and BB_EXIT in edge.dest.bb.flags:
          return

      style = ''
      edge_port = ''
      source_port = ''
      dest_port = ''

      if edge.kind in ('fallthrough', 'no fallthrough',
                         'follow', 'exit edge', 'dom-edge', 'pdom-edge'):
          if edge.kind == 'follow':
              style = '[style="invis"]'
              pass
          if edge.kind != 'exit edge':
              weight = 10
      elif edge.kind == 'exception':
          style = '[color="red"]'
          if edge.source.bb.number + 1 == edge.dest.bb.number:
              weight = 10
          else:
              weight = 1
              if BB_END_FINALLY in edge.dest.bb.flags:
                  source_port =':e'
              else:
                  source_port =':se'
              dest_port =':ne'
          # edge_port = '[headport=nw] [tailport=sw]';
          # edge_port = '[headport=_] [tailport=_]';
      else:
            if edge.kind == 'forward_scope':
                style = '[style="dotted"]'
                if edge.source.bb.number + 1 == edge.dest.bb.number:
                    weight = 10
                    source_port =':c'
                    dest_port =':c'
                else:
                    weight = 1
                    source_port =':se'
                    dest_port =':ne'
                pass
            elif edge.kind == 'self-loop':
                edge_port = '[headport=ne] [tailport=se]';
                pass
            elif edge.kind == 'backward':
                if edge.dest.bb.number + 1 == edge.source.bb.number:
                    # For a loop to the immmediate predecessor we use
                    # a somewhat straight centered backward arrow.
                    source_port =':c'
                    dest_port =':c'
                else:
                    source_port =':nw'
                    dest_port =':sw'
                    pass
            # FIXME: these edges need to come earlier
            # elif BB_JUMP_UNCONDITIONAL in edge.source.flags:
            #     source_port =':sw'
            #     dest_port =':nw'
            #     pass

            weight = 1
            pass

      if BB_EXIT in edge.dest.flags:
            style = '[style="dotted"] [arrowhead="none"]'
            if edge.source.bb.number + 1 == edge.dest.bb.number:
                weight = 10
                source_port =':c'
                dest_port =':c'
            else:
                weight = 1
                source_port =':se'
                dest_port =':ne'
                pass
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
          if edge_seen:
              return
          style = '[style="invis"]'

      nid1 = self.node_ids[edge.source]
      nid2 = self.node_ids[edge.dest]

      self.buffer += ('  %s%s -> %s%s [weight=%d]%s%s;\n' %
                        (nid1, source_port, nid2, dest_port,
                         weight, style, edge_port))

  @staticmethod
  def node_repr(node, align, is_exit):
      jump_text = ""
      if not is_exit and len(node.jump_offsets) > 0:
          jump_text = "\ljumps=%s" % sorted(node.jump_offsets)
          pass

      if node.flags:
          flag_text = "%s%s%s" % (align, flags_prefix,
                                  format_flags_with_width(node.flags, NODE_TEXT_WIDTH - FEL,
                                                          align + (" " * (len("flags=")))))
      else:
          flag_text = ""
          pass

      if is_exit:
          return "flags=exit"

      reach_offset_text = ""
      if hasattr(node, 'reach_offset'):
          reach_offset_text = "\lreach_offset=%d" % node.reach_offset

      offset_text = "offset: %d..%d" % (node.start_offset, node.end_offset)
      l = len(offset_text)
      if l < NODE_TEXT_WIDTH:
          offset_text += (' ' * (NODE_TEXT_WIDTH - l))


      return ('%s%s%s%s'
            % (offset_text, flag_text, jump_text, reach_offset_text))


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
      self.buffer += '  block_%d %s%s;\n' % (node.number, style, label)

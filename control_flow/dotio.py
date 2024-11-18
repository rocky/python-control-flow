# -*- coding: utf-8 -*-
# Copyright (c) 2021, 2024 by Rocky Bernstein <rb@dustyfeet.com>
"""
  Converts graph to dot format

  :copyright: (c) 2018, 2024 by Rocky Bernstein
  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
"""

from typing import Final, Optional, Tuple
from control_flow.bb import BasicBlock
from control_flow.graph import (
    DiGraph,
    BB_ENTRY,
    BB_EXIT,
    BB_END_FINALLY,
    BB_JOIN_NODE,
    BB_JUMP_TO_FALLTHROUGH,
    BB_JUMP_UNCONDITIONAL,
    BB_NOFOLLOW,
    ScopeEdgeKind,
    format_flags_with_width,
)

DOT_STYLE: Final = """
  graph[fontsize=10 fontname="DejaVu Sans Mono"];

  mclimit=1.5;
  rankdir=TD; ordering=out;
  color="#efefef";

  node[shape=box style=filled fontsize=10 fontname="DejaVu Sans Mono"
       fillcolor="#efefef", width=2];
  edge[fontsize=10 fontname="Verdana"];
"""

BB_LEVEL_BACKGROUNDS = (
    {"name": "DodgerBlue4", "hex": "#104e8b", "bg": "white"},
    {"name": "DodgerBlue3", "hex": "#1874cd", "bg": "white"},
    {"name": "DodgerBlue2", "hex": "#1c86ee", "bg": "white"},
    {"name": "DodgerBlue1", "hex": "#1e90ff", "bg": "white"},
    {"name": "SteelBlue2", "hex": "#5cacee", "bg": "black"},
    {"name": "SteelBlue1", "hex": "#63b8ff", "bg": "black"},
    {"name": "LightSteelBlue3", "hex": "#a2b5cd", "bg": "black"},
    {"name": "LightSteelBlue2", "hex": "#bcd2ee", "bg": "black"},
    # {"name": "SlateGray2", "hex": "#b9d3ee", "bg": "black"},
    {"name": "LightSteelBlue1", "hex": "#cae1ff", "bg": "black"},
)

MAX_COLOR_LEVELS: Final = len(BB_LEVEL_BACKGROUNDS) - 1

flags_prefix: Final = "flags="
FEL: Final = len(flags_prefix)
NODE_TEXT_WIDTH = 26 + FEL


class DotConverter:
    def __init__(self, graph):
        self.g = graph
        self.exit_node = graph
        self.buffer = ""
        self.node_ids = {}

    def get_node_colors(self, nesting_depth: int) -> Tuple[str, str]:
        if self.g.max_nesting < 0 or nesting_depth == -1:
            return "white", "black"
        if nesting_depth <= MAX_COLOR_LEVELS:
            color_info = BB_LEVEL_BACKGROUNDS[-(nesting_depth + 1)]
        else:
            level_index = round(
                1.0 / (nesting_depth * (self.g.max_nesting + 1)) * MAX_COLOR_LEVELS
            )
            color_info = BB_LEVEL_BACKGROUNDS[level_index]

        return color_info["hex"], color_info["bg"]

    @staticmethod
    def process(graph, exit_node: BasicBlock, is_dominator_format: bool):
        converter = DotConverter(graph)
        converter.run(exit_node, is_dominator_format)
        return converter.buffer

    # See Stackoverflow link below for information on how improve
    # layout of graph. It's a mess and not very well understood.
    def run(self, exit_node: BasicBlock, is_dominator_format: bool):
        self.buffer += "digraph G {"
        self.buffer += DOT_STYLE

        if isinstance(self.g, DiGraph):
            self.buffer += "\n  # basic blocks:\n"
            for node in sorted(self.g.nodes, key=lambda n: n.number):
                self.node_ids[node] = "block_%d" % node.number
                self.add_node(node, exit_node, is_dominator_format)

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
            for edge in sorted(
                self.g.edges,
                reverse=True,
                key=lambda n: (n.source.number, -n.dest.number),
            ):
                edge_pair = (edge.source.number, edge.dest.number)
                self.add_edge(edge, exit_node, edge_pair in seen_edge)
                seen_edge.add(edge_pair)

        self.buffer += "}\n"

    def add_edge(self, edge, exit_node: BasicBlock, edge_seen):
        # labels = ''
        # if edge.flags is not None:
        #   bb = '' if edge.bb is None else str(edge.bb)
        #   labels = '[label="%s - %s"]' % (edge.flags, bb)

        # color="black:invis:black"]

        if exit_node is not None and BB_EXIT in edge.dest.bb.flags:
            return

        style = ""
        edge_port = ""
        source_port = ""
        dest_port = ""
        weight = 1

        if edge.scoping_kind == ScopeEdgeKind.InnerJoin:
            arrow_color = ":brown;0.01"
        else:
            arrow_color = ""

        color = f'[color="blue:{arrow_color}"]' if edge.is_conditional_jump() else ""

        if edge.kind in (
            "fallthrough",
            "no fallthrough",
            "follow",
            "exit edge",
            "dom-edge",
            "pdom-edge",
        ):
            if edge.kind == "follow":
                style = '[style="invis"]'
            elif edge.kind == "fallthrough":
                color = f'[color="red{arrow_color}"]'
                pass
            if edge.kind != "exit edge":
                weight = 10
        elif edge.kind == "exception":
            style = f'[color="red{arrow_color}"]'
            if edge.source.bb.number + 1 == edge.dest.bb.number:
                weight = 10
            else:
                weight = 1
                if BB_END_FINALLY in edge.dest.bb.flags:
                    source_port = ":e"
                else:
                    source_port = ":se"
                dest_port = ":ne"
            # edge_port = '[headport=nw] [tailport=sw]';
            # edge_port = '[headport=_] [tailport=_]';
        else:
            if edge.kind == "forward-scope":
                style = '[style="dotted"]'
                if edge.source.bb.number + 1 == edge.dest.bb.number:
                    weight = 10
                    source_port = ":c"
                    dest_port = ":c"
                else:
                    weight = 1
                    source_port = ":se"
                    dest_port = ":ne"
                pass
            elif edge.kind == "self-loop":
                edge_port = f"[headport=ne, tailport=se, color='#006400'{arrow_color}]"
                pass
            elif edge.kind == "looping":
                if edge.dest.bb.number + 1 == edge.source.bb.number:
                    # For a loop to the immediate predecessor we use
                    # a somewhat straight centered backward arrow.
                    source_port = ":c"
                    dest_port = ":c"
                else:
                    color = f'[color="#006400"{arrow_color}]'
                    source_port = ":nw"
                    dest_port = ":sw"
                    pass
            # FIXME: these edges need to come earlier
            # elif BB_JUMP_UNCONDITIONAL in edge.source.flags:
            #     source_port =':sw'
            #     dest_port =':nw'
            #     pass

            elif BB_JUMP_TO_FALLTHROUGH in edge.source.flags:
                weight = 10
            else:
                weight = 1
            pass

        if BB_EXIT in edge.dest.flags:
            style = '[style="dotted"] [arrowhead="none"]'
            if edge.source.bb.number + 1 == edge.dest.bb.number:
                weight = 10
                source_port = ":c"
                dest_port = ":c"
            else:
                weight = 1
                source_port = ":se"
                dest_port = ":ne"
                pass
        elif BB_NOFOLLOW in edge.source.flags:
            style = '[style="dashed"] [arrowhead="none"]'
            weight = 10

        if style == "" and edge.source.bb.unreachable:
            style = '[style="dashed"] [arrowhead="empty"]'

        if edge.dest.bb.unreachable:
            style = '[style="dashed"] [arrowhead="empty"]'
            pass

        if edge.kind == "fallthrough":
            if BB_JUMP_UNCONDITIONAL in edge.source.flags:
                # style = '[color="black:invis:black"]'
                # style = '[style="dotted"] [arrowhead="empty"]'
                if edge_seen:
                    return
                style = '[style="invis"]'
            else:
                style = '[style="dashed"]'
        elif edge.kind == "forward-conditional":
            style = '[style="dotted"]'

        nid1 = self.node_ids[edge.source]
        nid2 = self.node_ids[edge.dest]

        self.buffer += "  %s%s -> %s%s [weight=%d]%s%s%s;\n" % (
            nid1,
            source_port,
            nid2,
            dest_port,
            weight,
            color,
            style,
            edge_port,
        )

    def node_repr(self, node, align, is_exit, is_dominator_format: bool):
        jump_text = ""
        reach_offset_text = ""
        flag_text = ""
        if not is_dominator_format:
            if not is_exit and len(node.jump_offsets) > 0:
                jump_text = f"\\ljumps={sorted(node.jump_offsets)}"
                pass

            if node.flags:
                flag_text = "%s%s%s" % (
                    align,
                    flags_prefix,
                    format_flags_with_width(
                        node.flags,
                        NODE_TEXT_WIDTH - FEL,
                        align + (" " * (len("flags="))),
                    ),
                )
            else:
                flag_text = ""
                pass

            if hasattr(node, "reach_offset"):
                reach_offset_text = "\\lreach_offset=%d" % node.reach_offset
                pass
            pass

        if is_exit:
            return "flags=exit"

        offset_text = "offset: %d..%d" % (node.start_offset, node.end_offset)
        l = len(offset_text)
        if l < NODE_TEXT_WIDTH:
            offset_text += " " * (NODE_TEXT_WIDTH - l)

        return f"{offset_text}{flag_text}{jump_text}{reach_offset_text}"

    def add_node(
        self, node, exit_node: Optional[BasicBlock], is_dominator_format: bool
    ):

        if exit_node is not None and BB_EXIT in node.bb.flags:
            return

        label = ""
        style = ""
        align = "\\l"

        is_exit = False
        dom_set_len = len(node.bb.dom_set)
        if exit_node in {node.bb for node in node.bb.dom_set}:
            dom_set_len -= 1
        if BB_ENTRY in node.bb.flags or dom_set_len > 0:
            style = '[shape = "box3d"]'
        elif BB_EXIT in node.bb.flags:
            style = '[shape = "diamond"]'
            align = "\n"
            is_exit = True
        elif not node.bb.predecessors:
            style = '[style = "dashed"]'
            pass

        if is_dominator_format:
            fillcolor, fontcolor = self.get_node_colors(node.bb.nesting_depth)
            # print("XXX", node.bb, node.bb.nesting_depth, fillcolor, fontcolor)
            color = 'color=brown, ' if BB_JOIN_NODE in node.bb.flags else ""
            style += f'[{color}fontcolor = "{fontcolor}", fillcolor = "{fillcolor}"]'

        level = " (%d)" % (node.bb.nesting_depth) if node.bb.nesting_depth >= 0 else ""

        label = '[label="Basic Block %d%s%s%s%s"]' % (
            node.number,
            level,
            align,
            self.node_repr(node.bb, align, is_exit, is_dominator_format),
            align,
        )
        self.buffer += "  block_%d %s%s;\n" % (node.number, style, label)

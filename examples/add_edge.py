BB_ENTRY = 1
BB_EXIT = 2
BB_NOFOLLOW = 3
BB_JUMP_UNCONDITIONAL= 3
DOT_STYLE = ""

def testing(self, edge, show_exit):

    self.buffer += 'digraph G {'
    self.buffer += DOT_STYLE

    if isinstance(self.g, list):
        self.buffer += "\n  # nodes:\n"
        for node in sorted(self.g.nodes, key=lambda n: n.number):
            self.node_ids[node] = 'node_%d' % node.number
            self.add_node(node, show_exit)

        self.buffer += "\n  # edges:\n"
        for edge in self.g.edges:
            self.add_edge(edge, show_exit)
import sys
def expect():
    if (sys.version_info[0:2] in ((3, 6), (3, 7))):
        return """
if BasicBlock(#0 range: (0, 38), flags=[0, 14], follow_offset=40, edge_count=2, jumps=[156])
  loop BasicBlock(#1 range: (40, 74), flags=[2], follow_offset=76, edge_count=2, jumps=[112])
    for BasicBlock(#2 range: (76, 76), flags=[9], follow_offset=78, edge_count=2, jumps=[110])
      continue BasicBlock(#3 range: (78, 108), flags=[8], follow_offset=110, edge_count=2, jumps=[76])
    end for
    pop block BasicBlock(#4 range: (110, 110), flags=[5], follow_offset=112, edge_count=1)
  end loop
  loop BasicBlock(#5 range: (112, 134), flags=[2], follow_offset=136, edge_count=2, jumps=[156])
    for BasicBlock(#6 range: (136, 136), flags=[9], follow_offset=138, edge_count=2, jumps=[154])
      continue BasicBlock(#7 range: (138, 152), flags=[8], follow_offset=154, edge_count=2, jumps=[136])
    end for
    pop block BasicBlock(#8 range: (154, 154), flags=[5], follow_offset=156, edge_count=1)
  end loop
end if
sequence BasicBlock(#9 range: (156, 158), flags=[1], follow_offset=None, edge_count=0)
"""
    elif (sys.version_info[0:2] == (2, 7)):
        return """
if BasicBlock(#0 range: (0, 45), flags=[0, 14], follow_offset=48, edge_count=2, jumps=[194])
  loop BasicBlock(#1 range: (48, 90), flags=[2], follow_offset=91, edge_count=2, jumps=[137])
    for BasicBlock(#2 range: (91, 91), flags=[9], follow_offset=94, edge_count=2, jumps=[136])
      continue BasicBlock(#3 range: (94, 133), flags=[8], follow_offset=136, edge_count=2, jumps=[91])
    end for
    pop block BasicBlock(#4 range: (136, 136), flags=[5], follow_offset=137, edge_count=1)
  end loop
  loop BasicBlock(#5 range: (137, 164), flags=[2], follow_offset=165, edge_count=2, jumps=[194])
    for BasicBlock(#6 range: (165, 165), flags=[9], follow_offset=168, edge_count=2, jumps=[190])
      continue BasicBlock(#7 range: (168, 187), flags=[8], follow_offset=190, edge_count=2, jumps=[165])
    end for
    sequence BasicBlock(#8 range: (190, 191), flags=[6, 8, 15], follow_offset=194, edge_count=2, jumps=[194])
  end loop
end if
"""

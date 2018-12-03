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
def expect():
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

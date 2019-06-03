# Compare with while3.py - the difference is a single jump location in bytecode.

# Note: driver assumes functions named "testing" and "expect".
def testing(a):
    while a:
        a += 2
    else:
        a += 1
    return a

def expect():
    return """
loop BasicBlock(#0 range: (0, 0), flags=[0, 2], follow_offset=2, edge_count=2, jumps=[26])
  while_else BasicBlock(#1 range: (2, 4), flags=[14], follow_offset=6, edge_count=2, jumps=[16])
    continue BasicBlock(#2 range: (6, 14), flags=[8], follow_offset=16, edge_count=2, jumps=[2])
    sequence pop block "while_else" BasicBlock(#3 range: (16, 24), flags=[6], follow_offset=26, edge_count=1)
  end while_else
end loop
sequence BasicBlock(#4 range: (26, 28), flags=[1], follow_offset=None, edge_count=0)
"""

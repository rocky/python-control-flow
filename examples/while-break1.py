# Note: driver assumes a function with the same name as the file basename
# test
def testing(a):
    while a:
        a -= 1
        break
        pass

def expect():
    return """
loop BasicBlock(#0 range: (0, 0), flags=[0, 2], follow_offset=2, edge_count=2, jumps=[18])
  while BasicBlock(#1 range: (2, 4), flags=[14], follow_offset=6, edge_count=2, jumps=[16])
    continue BasicBlock(#2 range: (6, 14), flags=[8], follow_offset=16, edge_count=2, jumps=[2])
  end while
  pop block BasicBlock(#3 range: (16, 16), flags=[5], follow_offset=18, edge_count=1)
end loop
sequence BasicBlock(#4 range: (18, 20), flags=[1], follow_offset=None, edge_count=0)
"""

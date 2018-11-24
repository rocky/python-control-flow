# Note: driver assumes a function with the same name as the file basename
# test
def testing(a):
    return a

def expect():
    return """
if BasicBlock(#0 range: (0, 2), flags=[0], follow_offset=4, edge_count=2, jumps=[12])
  then BasicBlock(#1 range: (4, 10), follow_offset=12, edge_count=1)
  end then
  sequence BasicBlock(#2 range: (12, 14), flags=[1], follow_offset=None, edge_count=0)
  end sequence
end if
"""

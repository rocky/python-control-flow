# Note: driver assumes functions named "testing" and "expect".
def testing(a):
    if a:
        return 5
    else:
        return 6
def expect():
    return """
if BasicBlock(#0 range: (0, 2), flags=[0, 14], follow_offset=4, edge_count=2, jumps=[8])
  then BasicBlock(#1 range: (4, 6), flags=[1], follow_offset=8, edge_count=0)
    sequence BasicBlock(#1 range: (4, 6), flags=[1], follow_offset=8, edge_count=0)
  end then
end if
no follow BasicBlock(#2 range: (8, 10), flags=[1], follow_offset=12, edge_count=0)
"""

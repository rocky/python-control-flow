# Note: driver assumes functions named "testing" and "expect".
def testing(a):
    if a:
        a += 1
    return a

def expect():
    return """
if BasicBlock(#0 range: (0, 2), flags=[0, 14], follow_offset=4, edge_count=2, jumps=[12])
  then BasicBlock(#1 range: (4, 10), follow_offset=12, edge_count=1)
    sequence BasicBlock(#1 range: (4, 10), follow_offset=12, edge_count=1)
  end then
end if
sequence BasicBlock(#2 range: (12, 14), flags=[1], follow_offset=None, edge_count=0)
"""

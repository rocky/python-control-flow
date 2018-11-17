# Note: driver assumes a function with the same name as the file basename
# test
def testing(a):
    if a:
        return 5
    return 6

def expect():
    return """
    if BasicBlock(#0 range: (0, 2), flags=[0], follow_offset=4, edge_count=2, jumps=[8])
  then BasicBlock(#1 range: (4, 6), flags=[1], follow_offset=8, edge_count=0)
  end then
end if
no follow BasicBlock(#2 range: (8, 10), flags=[1], follow_offset=None, edge_count=0)
"""

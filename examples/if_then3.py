# Note: driver assumes a function with the same name as the file basename
# test
# We can't distinguish between if_then3
# and if_then4
def testing(a):
    if a:
        return 5
    else:
        return 6

import sys
def expect():
    if (sys.version_info[0:2] in ((3, 6), (3, 7))):
        return """
if BasicBlock(#0 range: (0, 2), flags=[0, 14], follow_offset=4, edge_count=2, jumps=[8])
  then BasicBlock(#1 range: (4, 6), flags=[1], follow_offset=8, edge_count=0)
    sequence BasicBlock(#1 range: (4, 6), flags=[1], follow_offset=8, edge_count=0)
  end then
end if
no follow BasicBlock(#2 range: (8, 10), flags=[1], follow_offset=12, edge_count=0)
"""
    elif (sys.version_info[0:2] > (3, 0)):
        return """
if BasicBlock(#0 range: (0, 3), flags=[0, 14], follow_offset=6, edge_count=2, jumps=[10])
  then BasicBlock(#1 range: (6, 9), flags=[1], follow_offset=10, edge_count=0)
    sequence BasicBlock(#1 range: (6, 9), flags=[1], follow_offset=10, edge_count=0)
  end then
end if
no follow BasicBlock(#2 range: (10, 13), flags=[1], follow_offset=14, edge_count=0)
"""
    elif (sys.version_info[0:2] == (2, 7)):
        return """
if BasicBlock(#0 range: (0, 3), flags=[0, 14], follow_offset=6, edge_count=2, jumps=[10])
  then BasicBlock(#1 range: (6, 9), flags=[1], follow_offset=10, edge_count=0)
    sequence BasicBlock(#1 range: (6, 9), flags=[1], follow_offset=10, edge_count=0)
  end then
end if
no follow BasicBlock(#2 range: (10, 13), flags=[1], follow_offset=14, edge_count=0)
"""

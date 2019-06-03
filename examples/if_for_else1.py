# Note: driver assumes functions named "testing" and "expect".
def testing(a):
    if a:
        for i in range(3):
            a += 1
    else:
        a = 10

def expect():
    return """
if BasicBlock(#0 range: (0, 2), flags=[0, 14], follow_offset=4, edge_count=2, jumps=[32])
  loop BasicBlock(#1 range: (4, 12), flags=[2], follow_offset=14, edge_count=2, jumps=[36])
    for BasicBlock(#2 range: (14, 14), flags=[9], follow_offset=16, edge_count=2, jumps=[28])
      continue BasicBlock(#3 range: (16, 26), flags=[8], follow_offset=28, edge_count=2, jumps=[14])
    end for
    sequence BasicBlock(#4 range: (28, 30), flags=[6, 8], follow_offset=32, edge_count=2, jumps=[36])
  end loop
  else BasicBlock(#5 range: (32, 34), follow_offset=36, edge_count=1)
end if
"""

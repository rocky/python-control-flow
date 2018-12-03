# Note: driver assumes a function with the same name as the file basename
# test
def testing(a):
    if a:
        for i in range(3):
            a += 1
        else:
            a = 10

def expect():
    return """
if BasicBlock(#0 range: (0, 2), flags=[0, 14], follow_offset=4, edge_count=2, jumps=[34])
  loop BasicBlock(#1 range: (4, 12), flags=[2], follow_offset=14, edge_count=2, jumps=[34])
    for else BasicBlock(#2 range: (14, 14), flags=[9], follow_offset=16, edge_count=2, jumps=[28])
      continue BasicBlock(#3 range: (16, 26), flags=[8], follow_offset=28, edge_count=2, jumps=[14])
      sequence pop block "for else" BasicBlock(#4 range: (28, 32), flags=[6], follow_offset=34, edge_count=1)
    end for else
  end loop
end if
sequence BasicBlock(#5 range: (34, 36), flags=[1], follow_offset=None, edge_count=0)
"""

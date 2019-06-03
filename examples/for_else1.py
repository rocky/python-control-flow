# Note: driver assumes functions named "testing" and "expect".
def testing(a):
    for i in range(5):
        print(i)
    else:
        a = 5
    return a

def expect():
    return """
loop BasicBlock(#0 range: (0, 8), flags=[0, 2], follow_offset=10, edge_count=2, jumps=[30])
  for else BasicBlock(#1 range: (10, 10), flags=[9], follow_offset=12, edge_count=2, jumps=[24])
    continue BasicBlock(#2 range: (12, 22), flags=[8], follow_offset=24, edge_count=2, jumps=[10])
    sequence pop block "for else" BasicBlock(#3 range: (24, 28), flags=[6], follow_offset=30, edge_count=1)
  end for else
end loop
sequence BasicBlock(#4 range: (30, 32), flags=[1], follow_offset=None, edge_count=0)
"""

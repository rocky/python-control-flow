# Note: driver assumes a function with the same name as the file basename
# test
def testing(a):
    for i in range(5):
        print(i)
    else:
        a = 5

def expect():
    return """
loop BasicBlock(#0 range: (0, 8), flags=[0, 2], follow_offset=10, edge_count=2, jumps=[30])
  for else BasicBlock(#1 range: (10, 10), flags=[9], follow_offset=12, edge_count=2, jumps=[24])
    continue BasicBlock(#2 range: (12, 22), flags=[8], follow_offset=24, edge_count=2, jumps=[10])
    sequence pop block "for else" BasicBlock(#3 range: (24, 28), flags=[6], follow_offset=30, edge_count=1)
    end sequence pop block "for else"
  end for else
end loop
"""

# Note: driver assumes a function with the same name as the file basename
# test
def testing(a):
    for i in range(5):
        print(i)

def expect():
    return """
    loop BasicBlock(#0 range: (0, 8), flags=[0, 2], follow_offset=10, edge_count=2, jumps=[26])
  for BasicBlock(#1 range: (10, 22), flags=[8, 9], follow_offset=24, edge_count=2, jumps=[10])
  end for
end loop
"""

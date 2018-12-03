# Note: driver assumes a function with the same name as the file basename
# test
def testing(a, b):
    if a \
       and b:
        c = 1
    if a:
        if b:
            c = 2
    return c
def expect():
    return """
if BasicBlock(#0 range: (0, 2), flags=[0, 14], follow_offset=4, edge_count=2, jumps=[12])
  then BasicBlock(#1 range: (4, 6), flags=[14], follow_offset=8, edge_count=2, jumps=[12])
    if BasicBlock(#1 range: (4, 6), flags=[14], follow_offset=8, edge_count=2, jumps=[12])
      then BasicBlock(#2 range: (8, 10), follow_offset=12, edge_count=1)
        sequence BasicBlock(#2 range: (8, 10), follow_offset=12, edge_count=1)
      end then
    end if
  end then
  sequence BasicBlock(#3 range: (12, 14), flags=[14], follow_offset=16, edge_count=2, jumps=[24])
  if BasicBlock(#3 range: (12, 14), flags=[14], follow_offset=16, edge_count=2, jumps=[24])
    then BasicBlock(#4 range: (16, 18), flags=[14], follow_offset=20, edge_count=2, jumps=[24])
      if BasicBlock(#4 range: (16, 18), flags=[14], follow_offset=20, edge_count=2, jumps=[24])
        then BasicBlock(#5 range: (20, 22), follow_offset=24, edge_count=1)
          sequence BasicBlock(#5 range: (20, 22), follow_offset=24, edge_count=1)
        end then
      end if
    end then
  end if
  end sequence
end if
sequence BasicBlock(#6 range: (24, 26), flags=[1], follow_offset=None, edge_count=0)
"""

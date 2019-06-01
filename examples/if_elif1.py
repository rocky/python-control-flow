# Note: driver assumes a function named "testing"
def testing(a):
    if a == 10:
        print(0)
    else:
        if 11 <= a <= 15:
            for i in range(10):
                print(i)
        else:
            print(3)

def expect():
    return """
if BasicBlock(#0 range: (0, 6), flags=[0, 14], follow_offset=8, edge_count=2, jumps=[18])
  then BasicBlock(#1 range: (8, 16), flags=[8], follow_offset=18, edge_count=2, jumps=[78])
    sequence BasicBlock(#1 range: (8, 16), flags=[8], follow_offset=18, edge_count=2, jumps=[78])
  end then
  else BasicBlock(#2 range: (18, 28), flags=[14], follow_offset=30, edge_count=2, jumps=[38])
    if BasicBlock(#2 range: (18, 28), flags=[14], follow_offset=30, edge_count=2, jumps=[38])
      then BasicBlock(#3 range: (30, 34), flags=[14], follow_offset=36, edge_count=2, jumps=[70])
        if BasicBlock(#3 range: (30, 34), flags=[14], follow_offset=36, edge_count=2, jumps=[70])
          then BasicBlock(#4 range: (36, 36), flags=[8], follow_offset=38, edge_count=2, jumps=[42])
            sequence BasicBlock(#4 range: (36, 36), flags=[8], follow_offset=38, edge_count=2, jumps=[42])
            loop BasicBlock(#6 range: (42, 50), flags=[2], follow_offset=52, edge_count=2, jumps=[78])
              for BasicBlock(#7 range: (52, 52), flags=[9], follow_offset=54, edge_count=2, jumps=[66])
                continue BasicBlock(#8 range: (54, 64), flags=[8], follow_offset=66, edge_count=2, jumps=[52])
              end for
              sequence BasicBlock(#9 range: (66, 68), flags=[6, 8], follow_offset=70, edge_count=2, jumps=[78])
            end loop
        end if
      end then
      else BasicBlock(#5 range: (38, 40), flags=[8], follow_offset=42, edge_count=2, jumps=[70])
        sequence BasicBlock(#5 range: (38, 40), flags=[8], follow_offset=42, edge_count=2, jumps=[70])
        sequence BasicBlock(#10 range: (70, 76), follow_offset=78, edge_count=1)
        end sequence
      end else
    end if
  end else
end if
"""

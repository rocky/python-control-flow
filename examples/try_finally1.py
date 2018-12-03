# Note: driver assumes a function with the same name as the file basename
# test
def testing(a):
    try:
        a += 1
    except:
        a += 2
    finally:
        a = 3


def expect():
    return """
finally BasicBlock(#0 range: (0, 0), flags=[0, 10], follow_offset=2, edge_count=2, jumps=[40])
  try BasicBlock(#1 range: (2, 14), flags=[4, 8, 11], follow_offset=16, edge_count=2, jumps=[36], exceptions=[16, 34, 40])
    except BasicBlock(#2 range: (16, 32), flags=[7, 8], follow_offset=34, edge_count=2, jumps=[36])
    end-finally BasicBlock(#3 range: (34, 34), flags=[12], follow_offset=36, edge_count=1)
    end end-finally
    end-finally BasicBlock(#5 range: (40, 48), flags=[1, 12], follow_offset=None, edge_count=0)
    end end-finally
    try else BasicBlock(#4 range: (36, 38), flags=[6], follow_offset=40, edge_count=1)
  end try
end finally
"""

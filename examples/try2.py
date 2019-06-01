# Note: driver assumes functions named "testing" and "expect".
def testing(a):
    try:
        a += 1
    except:
        a += 2
    a = 3


def expect():
    return """
try BasicBlock(#0 range: (0, 12), flags=[0, 4, 8, 11], follow_offset=14, edge_count=2, jumps=[34], exceptions=[14, 32])
  except BasicBlock(#1 range: (14, 30), flags=[7, 8], follow_offset=32, edge_count=2, jumps=[34])
  end-finally BasicBlock(#2 range: (32, 32), flags=[12], follow_offset=34, edge_count=1)
  end end-finally
end try
sequence BasicBlock(#3 range: (34, 40), flags=[1], follow_offset=None, edge_count=0)
"""

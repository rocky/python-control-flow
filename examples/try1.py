# Note: driver assumes a function with the same func_or_code_name as the file basename

# Note: driver assumes functions named "testing" and "expect".
def testing(a):
    try:
        a += 1
    except:
        a += 2


import sys
def expect():
    if (sys.version_info[0:2] in ((3, 6), (3, 7))):
        return """
try BasicBlock(#0 range: (0, 12), flags=[0, 4, 8, 11], follow_offset=14, edge_count=2, jumps=[34], exceptions=[14, 32])
  except BasicBlock(#1 range: (14, 30), flags=[7, 8], follow_offset=32, edge_count=2, jumps=[34])
  end-finally BasicBlock(#2 range: (32, 32), flags=[12], follow_offset=34, edge_count=1)
  end end-finally
end try
sequence BasicBlock(#3 range: (34, 36), flags=[1], follow_offset=None, edge_count=0)
"""
    elif (sys.version_info[0:2] == (2, 7)):
        return """
try BasicBlock(#0 range: (0, 14), flags=[0, 4, 8, 11], follow_offset=17, edge_count=2, jumps=[34], exceptions=[17, 33])
  except BasicBlock(#1 range: (17, 30), flags=[7, 8], follow_offset=33, edge_count=2, jumps=[34])
  end_finally BasicBlock(#2 range: (33, 33), flags=[12], follow_offset=34, edge_count=1)
end try
"""

# Note: driver assumes a function with the same name as the file basename
# test
def testing(a):
    try:
        a += 1
    except:
        a += 2
    else:
        a = 3


import sys
def expect():
    if (sys.version_info[0:2] in ((3, 6), (3, 7))):
        return """
try BasicBlock(#0 range: (0, 12), flags=[0, 4, 8, 11], follow_offset=14, edge_count=2, jumps=[34], exceptions=[14, 32])
  except BasicBlock(#1 range: (14, 30), flags=[7, 8], follow_offset=32, edge_count=2, jumps=[38])
  end_finally BasicBlock(#2 range: (32, 32), flags=[12], follow_offset=34, edge_count=1)
  try_else BasicBlock(#3 range: (34, 36), follow_offset=38, edge_count=1)
end try
"""
    elif (sys.version_info[0:2] > (3, 0)):
        return """
try BasicBlock(#0 range: (0, 14), flags=[0, 4, 8, 11], follow_offset=17, edge_count=2, jumps=[35], exceptions=[17, 34])
  except BasicBlock(#1 range: (17, 31), flags=[7, 8], follow_offset=34, edge_count=2, jumps=[41])
  end_finally BasicBlock(#2 range: (34, 34), flags=[12], follow_offset=35, edge_count=1)
  try_else BasicBlock(#3 range: (35, 38), follow_offset=41, edge_count=1)
end try
"""
    elif (sys.version_info[0:2] == (2, 7)):
        return """
try BasicBlock(#0 range: (0, 14), flags=[0, 4, 8, 11], follow_offset=17, edge_count=2, jumps=[34], exceptions=[17, 33])
  except BasicBlock(#1 range: (17, 30), flags=[7, 8], follow_offset=33, edge_count=2, jumps=[40])
  try_else BasicBlock(#3 range: (34, 37), follow_offset=40, edge_count=1)
  end_finally BasicBlock(#2 range: (33, 33), flags=[12], follow_offset=34, edge_count=1)
end try
"""

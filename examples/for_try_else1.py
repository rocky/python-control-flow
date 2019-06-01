# Bug found in 2.7 test_itertools.py

# Note: driver assumes a functions named "testing" and "expect".
def testing(self):

    # The bug was the except jumping back
    # to the beginning of this for loop
    for stmt in ["a", "b"]:
        try:
            eval(stmt)
        except TypeError:
            pass
        else:
            self.fail()
import sys
def expect():
    if (sys.version_info[0:2] in ((3, 6), (3, 7))):
        return """
loop BasicBlock(#0 range: (0, 4), flags=[0, 2], follow_offset=6, edge_count=2, jumps=[56])
  for BasicBlock(#1 range: (6, 6), flags=[9], follow_offset=8, edge_count=2, jumps=[54])
    try BasicBlock(#2 range: (8, 22), flags=[4, 8, 11], follow_offset=24, edge_count=2, jumps=[44], exceptions=[32, 42])
      except BasicBlock(#4 range: (32, 40), flags=[7, 8], follow_offset=42, edge_count=2, jumps=[6])
      end_finally BasicBlock(#5 range: (42, 42), flags=[12], follow_offset=44, edge_count=1)
      try_else_continue BasicBlock(#6 range: (44, 52), flags=[8], follow_offset=54, edge_count=2, jumps=[6])
    end try
  end for
  pop block BasicBlock(#7 range: (54, 54), flags=[5], follow_offset=56, edge_count=1)
end loop
sequence BasicBlock(#8 range: (56, 58), flags=[1], follow_offset=None, edge_count=0)
"""
    elif (sys.version_info[0:2] > (3, 0)):
        return """
loop BasicBlock(#0 range: (0, 12), flags=[0, 2], follow_offset=13, edge_count=2, jumps=[68])
  for BasicBlock(#1 range: (13, 13), flags=[9], follow_offset=16, edge_count=2, jumps=[67])
    try_else BasicBlock(#2 range: (16, 33), flags=[4, 8, 11], follow_offset=36, edge_count=2, jumps=[54], exceptions=[46, 53])
      except BasicBlock(#4 range: (46, 50), flags=[7, 8], follow_offset=53, edge_count=2, jumps=[13])
      end_finally BasicBlock(#5 range: (53, 53), flags=[12], follow_offset=54, edge_count=1)
      try_else_continue BasicBlock(#6 range: (54, 64), flags=[8], follow_offset=67, edge_count=2, jumps=[13])
    end try_else
  end for
  pop block BasicBlock(#7 range: (67, 67), flags=[5], follow_offset=68, edge_count=1)
end loop
sequence BasicBlock(#8 range: (68, 71), flags=[1], follow_offset=None, edge_count=0)
"""
    elif (sys.version_info[0:2] == (2, 7)):
        return """
loop BasicBlock(#0 range: (0, 12), flags=[0, 2], follow_offset=13, edge_count=2, jumps=[67])
  for BasicBlock(#1 range: (13, 13), flags=[9], follow_offset=16, edge_count=2, jumps=[66])
    try_else BasicBlock(#2 range: (16, 33), flags=[4, 8, 11], follow_offset=36, edge_count=2, jumps=[53], exceptions=[46, 52])
      except BasicBlock(#4 range: (46, 49), flags=[7, 8], follow_offset=52, edge_count=2, jumps=[13])
      end_finally BasicBlock(#5 range: (52, 52), flags=[12], follow_offset=53, edge_count=1)
      try_else_continue BasicBlock(#6 range: (53, 63), flags=[8], follow_offset=66, edge_count=2, jumps=[13])
    end try_else
  end for
  pop block BasicBlock(#7 range: (66, 66), flags=[5], follow_offset=67, edge_count=1)
end loop
sequence BasicBlock(#8 range: (67, 70), flags=[1], follow_offset=None, edge_count=0)
"""

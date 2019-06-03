# Bug found in 2.7 test_itertools.py

# Note: driver assumes functions named "testing" and "expect".
def testing(self):

    # The bug was the except jumping back
    # to the beginning of this for loop
    for stmt in ["a", "b"]:
        try:
            eval(stmt)
        except TypeError:
            pass
        self.fail()
import sys
def expect():
    if (sys.version_info[0:2] in ((3, 6), (3, 7))):
        return """
loop BasicBlock(#0 range: (0, 4), flags=[0, 2], follow_offset=6, edge_count=2, jumps=[56])
  for BasicBlock(#1 range: (6, 6), flags=[9], follow_offset=8, edge_count=2, jumps=[54])
    try BasicBlock(#2 range: (8, 22), flags=[4, 8, 11], follow_offset=24, edge_count=2, jumps=[44], exceptions=[32, 42])
      except BasicBlock(#4 range: (32, 40), flags=[7, 8], follow_offset=42, edge_count=2, jumps=[44])
      end_finally BasicBlock(#5 range: (42, 42), flags=[12], follow_offset=44, edge_count=1)
      continue BasicBlock(#6 range: (44, 52), flags=[8], follow_offset=54, edge_count=2, jumps=[6])
    end try
  end for
  pop block BasicBlock(#7 range: (54, 54), flags=[5], follow_offset=56, edge_count=1)
end loop
sequence BasicBlock(#8 range: (56, 58), flags=[1], follow_offset=None, edge_count=0)
"""

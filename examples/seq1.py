# Note: driver assumes a function with the same name as the file basename
# test
def testing(a):
    return a

def expect():
    return """
control_structure_iter:  BasicBlock(#0 range: (0, 2), flags=[0, 1], follow_offset=None, edge_count=0)
"""

# Note: driver assumes a function with the same name as the file basename
# test
def testing(a):
    a(3)

def expect():
    return """
control_structure_iter:  BasicBlock(#0 range: (0, 10), flags=[0, 1], follow_offset=None, edge_count=0)
"""

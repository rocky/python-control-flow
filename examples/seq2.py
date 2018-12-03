# Note: driver assumes a function with the same name as the file basename
# test
def testing(a):
    a = 2
    return a

def expect():
    return """
sequence BasicBlock(#0 range: (0, 6), flags=[0, 1], follow_offset=None, edge_count=0)
"""

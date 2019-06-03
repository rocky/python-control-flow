# Note: driver assumes functions named "testing" and "expect".
def testing(a):
    a(3)

def expect():
    return """
sequence BasicBlock(#0 range: (0, 10), flags=[0, 1], follow_offset=None, edge_count=0)
"""

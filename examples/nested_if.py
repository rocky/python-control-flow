# Note: driver assumes functions named "testing" and "expect".
def testing(a, b):
    if a:
        a += 1
        if b:
            a += 1
    return a

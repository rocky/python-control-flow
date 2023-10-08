# Note: driver assumes functions named "testing" and "expect".
def testing(a, b):
    if a:
        a += 1
        if b:
            a += 1
        else:
            a -= 2
        a += 10
    else:
        a -= 2
    if b:
        a -= 100
    else:
        a += 101
    return a

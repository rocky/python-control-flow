#!/usr/bin/env python
from control_flow.__main__ import doit


def err():
    x = "Foo"
    raise RuntimeError(x)


def five():
    return 5


def or1(a, b):
    return a or b


def if_else(a):
    if a:
        return 5
    else:
        return 6


def if_vs_and(a, b):
    if a and b:
        c = 1
    if a:
        if b:
            c = 2
    return c


def if_then0(a):
    if a:
        a += 1


def if_then1(a):
    if a:
        a += 1
    return a


def if_then2(a):
    if a:
        return 5


# We can't distinguish between if_then3
# and if_then4
def if_then3(a):
    if a:
        return 5
    else:
        return 6


def if_then4(a):
    if a:
        return 5
    return 6


def foo1(a):
    if a:
        a += 1
    else:
        a += 2
    return a


def foo2(a):
    if a:
        a = 10
    return a


def while_if_continue(a):
    a += 1
    while a > 5:
        if a:
            a += 1
            continue
        a -= 1


def while_true_if_else(a):
    while True:
        if a:
            a -= 1
        else:
            return 6


def while_else(a):
    while a:
        a += 2
    else:
        a = 5
    return a


def while_if(a):
    b = 0
    while a > 0:
        if a % 2:
            b += 1
        a >> 1
    return b


def for_break():
    for i in range(3):
        if i == 2:
            break
        else:
            continue


def try_finally():
    try:
        x = 1
    except RuntimeError:
        x = 2
    except:
        x = 3
    finally:
        x = 4
    return x


def try_no_finally():
    try:
        x = 1
    except RuntimeError:
        x = 2
    except:
        x = 3
    return x


def while_true_break():
    x = 0
    while True:
        try:
            x += 1
            break
        except Exception:
            pass


# doit(err)
# doit(or1)
# doit(if_then0)
# doit(if_then1)
# doit(if_then2)
# doit(if_then3)
# doit(if_then4)
# doit(five)
# doit(for_break)
# doit(if_else)
# doit(if_vs_and)
# doit(foo)
# doit(foo1)
# doit(foo2)
# doit(while_if_continue)
# doit(while_true_if_else)
# doit(while_else)
# doit(while_if)
# doit(while_true_break)
doit(try_finally)
doit(try_no_finally)

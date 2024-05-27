#!/usr/bin/env python
from control_flow.build_control_flow import build_and_analyze_control_flow


def err():
    x = "Foo"
    raise RuntimeError(x)


def five():
    return 5


def trivial_or(a, b):
    return a or b


def if_else(a):
    if a:
        a += 1
    else:
        a += 2
    return a

def if_else_return(a):
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

def if_else_expr(x):
    """An example "if expr1 else expr2 """
    return 1 if x else 5

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
        a >>= 1
    return b


def for_break():
    for i in range(3):
        if i == 2:
            break
        else:
            continue


def try_except():
    try:
        a = 1
    except:
        a = 2
    return a

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


def and_or(a, b, c, d, e, f, g, h):
    return (a and b and c and d) or (e or f or g or h)


def or_and(a, b, c, d, e, f, g, h):
    return (a or b or c or d) and (e and f and g and h)


def ifelif(a, b, c, x):
    if a:
        x = 1
    elif b:
        x = 2
    elif c:
        x = 3
    else:
        x = 4
    return x

# build_and_analyze_control_flow(err, graph_options="all")
build_and_analyze_control_flow(trivial_or, graph_options="all")
# build_and_analyze_control_flow(if_else_expr, graph_options="all")
# build_and_analyze_control_flow(ifelif, graph_options="all")
# build_and_analyze_control_flow(or_and)
# build_and_analyze_control_flow(and_or)
# build_and_analyze_control_flow(if_then0)
# build_and_analyze_control_flow(if_then1, graph_options="all")
# build_and_analyze_control_flow(if_then2)
# build_and_analyze_control_flow(if_then3)
# build_and_analyze_control_flow(if_then4, graph_options="all")
# build_and_analyze_control_flow(five)
# build_and_analyze_control_flow(for_break, graph_options="all")
# build_and_analyze_control_flow(if_else, graph_options="all")
# build_and_analyze_control_flow(if_else_return, graph_options="all")
# build_and_analyze_control_flow(if_vs_and, graph_options="all")
# build_and_analyze_control_flow(foo)
# build_and_analyze_control_flow(foo1)
# build_and_analyze_control_flow(foo2)
# build_and_analyze_control_flow(while_if_continue, graph_options="all")
# build_and_analyze_control_flow(while_true_if_else)
# build_and_analyze_control_flow(while_else)
# build_and_analyze_control_flow(while_if)
# build_and_analyze_control_flow(while_true_break)
# build_and_analyze_control_flow(try_except, graph_options="all")
# build_and_analyze_control_flow(try_finally)
# build_and_analyze_control_flow(try_no_finally)

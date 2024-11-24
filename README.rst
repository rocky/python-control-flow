Introduction
------------

This is a Toolkit for getting control flow information from Python bytecode.

Specifically:

* Creates basic blocks from Python bytecode.
* Creates control-flow graph from the basic blocks.
* Creates dominator trees and dominator regions for the control flow.
* Graphs via `dot <https://graphviz.org/>`_ the control-flow graph and dominator tree.


I've used some routines from Romain Gaucher's `equip <https://github.com/neuroo/equip>`_ as a starting point.

Example
-------

For now the Python in ``test/test_bb2.py`` show what's up the best.

Consider this simple Python program taken from my `BlackHat Asia 2024 talk <https://www.blackhat.com/asia-24/briefings/schedule/index.html#how-to-get-the-most-out-of-the-python-decompilers-uncompyle-and-decompyle---how-to-write-and-read-a-bytecode-decompiler-37789>`_:

.. code-block:: python

    # Program to count the number of bits in the integer 6.
    i: int = 6
    zero_bits = 0
    one_bits = 0
    while i > 0:  # loop point
       # loop alternative
       if i % 0:
           # first alternative
           one_bits += 1
       else:
           # second alternative
           zero_bits += 1
       # join point
       i << 1
    # loop-end join point

You can find this byte-compiled to Python 3.8 bytecode in `doc-example/count-bits.cpython-38.pyc <https://github.com/rocky/python-control-flow/blob/post-dominator-refactor/doc-example/count-bits.cpython-38.pyc>`_.
We can get control flow information for this program using::

  python ./test/test-bb2.py doc-example/count-bits.cpython-38.pyc

After running, in ``/tmp`` you'll find some ``.dot`` files and some ``.png`` images generated for the main routine.

``flow-3.8--count-bits.cpython-38--module.png`` is a PNG image for the control flow.

.. image:: https://github.com/rocky/python-control-flow/blob/master/doc-example/flow-3.8-count-bits.cpython-38--module.png

Here is what the colors on the arrows indicate:

red
    the first alternative of a group of two alternatives

blue
    the second alternative of a group of two alternatives

green
     a looping (backward) jump

Here is what the line styles on the arrows indicate:

solid
     an unconditional (and forward) jump

dashed
     This should always be shown as a straight line centered from one block on
     top to the next block below it. It is the block that follows in
     the bytecode sequentially. If there is an arrowhead, there is a
     fallthrough path from the upper block to the lower block. If there is no
     arrowhead, then either the last instruction of the upper basic-block
     is an unconditional jump or this instruction a return
     instruction or an explicit exception-raising instruction.

dotted
     the jump path of a conditional jump. This is usually curved
     and appears on the side of a box.


We align blocks linearly using the offset addresses. You can find
the offset ranges listed inside the block. The entry block is
marked with an additional border. We also show the basic block number
and block flags.

Any block that is ghost-like or has a white-background box in a
dashed border is dead code.

Control-Flow with Dominator Regions
+++++++++++++++++++++++++++++++++++

In addition to the basic control flow, we mark and color boxes with dominator regions.

.. image:: https://github.com/rocky/python-control-flow/blob/master/doc-example/flow%2Bdom-3.8-count-bits.cpython-38--module.png

Regions with the same nesting level have the same color. So Basic blocks 3 and 7 are at the same nesting level. Blocks 4 and 5 are at the same nesting level and color.

Block 6 has two jumps into it, so it is neither "inside" nor blocks 4 or 5. Block 6 is the "join point" block after an if/else::

   # block 3
   if i % 0:
       # block 4
       one_bits += 1
   else:
       # block 5
       zero_bits += 1
   # join point
   i << 1  # This is block 6

The collection of blocks 4, 5, and 6 are all dominated by the block region head Block 3 which has a border around it to show it is the head of a block region.

A border is put around a block *only* if it dominates some *other* block. So while technically block 4 dominates, itself, and block 5 dominates itself, that fact is not interesting.


Colors get darker as the region is more nested.


In addition, if a jump or fallthrough jumps out of its dominator region
the arrowhead of the jump is shown in brown. Note that a jump arrow
from an "if"-like statement or "for"-like to its end will not be in
brown. Only the "fallthrough" arrow will be in brown. This is why the
arrowhead of the jump from block to block 7 is blue, not brown.

If any basic block is jumped to using a jump-out (or end scope) kind of edge, then the box has a brown outline.

Inside the block text, we now add the dominator region number for a block in parenthesis. For example, Basic blocks, 4 and 5 are in dominator region 3 and so are marked "(3)" after their basic block number. The dominator number for a basic block is the same as its basic block number. So Basic Block 3 is also Dominator Region 3.

Note that even though basic blocks 4 and 5 are at the same indentation level, they are in different *scopes* under basic block 3.

In this example, all conditional jumps were taken if the condition was false. When the condition is true, we bold the dotted blue arrow. By doing this and by showing whether the jump condition is true or false, you can see in the control flow whether the source text contains an "and" type of condition or an "or" type of condition.

Here is the graph for ``x and y``:

.. image:: https://github.com/rocky/python-control-flow/blob/master/doc-example/flow%2Bdom-3.9-and-lambda%3Ax-y.png

Note the same graph would be the same as ``if x: if y: ...```.

The graph for ``a or b`` is almost the same except the style of the blue dotted arrow:

.. image:: https://github.com/rocky/python-control-flow/blob/master/doc-example/flow%2Bdom-3.9-or-lambda%3Aa-b.png

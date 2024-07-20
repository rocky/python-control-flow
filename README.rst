*Note: the branch `post-dominator-refactor branch README.rst <https://github.com/rocky/python-control-flow/blob/post-dominator-refactor/README.rst>`_ has the more information.*

This is a Toolkit for getting control flow informaion from Python bytecode

Specifically:

* creates basic blocks from Python bytecode
* creates control-flow graph from the basic blocks
* creates a dominator tree
* Graphs via dot the control-flow graph and dominator tree


I've used some routines from Romain Gaucher's equip as a starting point.
equip is (c) 2014 by Romain Gaucher

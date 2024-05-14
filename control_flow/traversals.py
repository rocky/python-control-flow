# -*- coding: utf-8 -*-
"""
  equip.analysis.graph.traversals
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  DFS and some other utils

  :copyright: (c) 2018, 2024 by Rocky Bernstein
  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""

from control_flow.graph import Edge


class EdgeVisitor:
    def __init__(self):
        pass

    def visit(self, edge):
        pass


class Walker:
    """
    Traverses edges in the graph in DFS.
    """

    def __init__(self, graph, visitor):
        self._graph = graph
        self._visitor = visitor
        self.worklist: list = []

    @property
    def graph(self):
        return self._graph

    @graph.setter
    def graph(self, value):
        self._graph = value

    @property
    def visitor(self):
        return self._visitor

    @visitor.setter
    def visitor(self, value):
        self._visitor = value
        return

    def traverse(self, root):
        self.worklist: list = []
        self.__run(root)
        return

    def __run(self, root=None):
        visited = set()
        if root is not None:
            self.__process(root)
        while self.worklist:
            current = self.worklist.pop(0)
            if current in visited:
                continue
            self.__process(current)
            visited.add(current)

    def __process(self, current):
        cur_node = None
        if isinstance(current, Edge):
            cur_node = current.dest
            self.visitor.visit(current)
        else:
            cur_node = current

        list_edges = cur_node.successors
        for edge in list_edges:
            self.worklist.insert(0, edge)


# Recursive version of the post-order DFS, should only be used
# when computing dominators on smallish CFGs


# FIXME: This assumes the graph is strongly connected.
# handle if it is a not.
def dfs_postorder_nodes(root):
    import sys

    sys.setrecursionlimit(5000)
    visited = set()

    def _dfs(node, _visited):
        _visited.add(node)
        successors = node.successors
        for dest_node in successors:
            if dest_node not in _visited:
                for child in _dfs(dest_node, _visited):
                    yield child
                    pass
                pass
            pass
        yield node
        return

    return [n for n in _dfs(root, visited)]

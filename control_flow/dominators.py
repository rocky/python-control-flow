# -*- coding: utf-8 -*-
"""
  Dominator tree

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
"""

from graph import DiGraph
from traversals import dfs_postorder_nodes


class DominatorTree(object):
  """
    Handles the dominator trees (dominator/post-dominator), and the
    computation of the dominance/post-dominance frontier.
  """

  def __init__(self, cfg):
    self.cfg = cfg
    self.doms = {}
    self.df = {}
    self.build()


  def build(self):
    graph = self.cfg.graph
    entry = self.cfg.entry_node
    self.build_dominators(graph, entry)
    # self.build_df(graph)


  def build_dominators(self, graph, entry):
    """
      Builds the dominator tree based on:
        http://www.cs.rice.edu/~keith/Embed/dom.pdf

      Also used to build the post-dominator tree.
    """
    doms = self.doms
    doms[entry] = entry
    post_order = dfs_postorder_nodes(graph, entry)

    post_order_number = {}
    i = 0
    for n in post_order:
      post_order_number[n] = i
      i += 1

    def intersec(b1, b2):
      finger1 = b1
      finger2 = b2
      po_finger1 = post_order_number[finger1]
      po_finger2 = post_order_number[finger2]
      while po_finger1 != po_finger2:
        no_solution = False
        while po_finger1 < po_finger2:
          finger1 = doms.get(finger1, None)
          if finger1 is None:
            no_solution = True
            break
          po_finger1 = post_order_number[finger1]
        while po_finger2 < po_finger1:
          finger2 = doms.get(finger2, None)
          if finger2 is None:
            no_solution = True
            break
          po_finger2 = post_order_number[finger2]
        if no_solution:
          break
      return finger1

    changed = True
    while changed:
      changed = False
      for b in reversed(post_order):
        if b == entry:
          continue
        predecessors = b.predecessors
        new_idom = next(iter(predecessors))
        for p in predecessors:
          if p == new_idom:
            continue
          if p in doms:
            new_idom = intersec(p, new_idom)
        if b not in doms or doms[b] != new_idom:
          doms[b] = new_idom
          changed = True
          pass
        pass
    return

  def build_df(self, graph):
    """
      Builds the dominance frontier.
    """
    doms = self.doms
    df = self.df

    for b in graph.nodes:
      df[b] = set()

    for b in graph.nodes:
      predecessors = b.bb.predecessors
      if len(predecessors) > 1:
        for p in predecessors:
          runner = p
          while runner != doms[b.bb]:
            df[runner].add(b)
            runner = doms[runner]

  def tree(self):
    g_nodes = {}
    doms = self.doms
    g = DiGraph()

    for node in doms:
      if node not in g_nodes:
        cur_node = g.make_add_node(node)
        g_nodes[node] = cur_node
      cur_node = g_nodes[node]

      parent = doms.get(node, None)
      if parent is not None and parent != node:
        if parent not in g_nodes:
          parent_node = g.make_add_node(parent.flags, parent)
          g_nodes[parent] = parent_node
        parent_node = g_nodes[parent]
        g.make_add_edge(parent_node, cur_node, 'fall-through')

    return g

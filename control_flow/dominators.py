1# -*- coding: utf-8 -*-
"""
  Dominator tree

  Copyright (c) 2017-2018 by Rocky Bernstein
  Copyright (c) 2014 by Romain Gaucher (@rgaucher)
"""

from control_flow.graph import TreeGraph
from control_flow.traversals import dfs_postorder_nodes


class DominatorTree(object):
    """
      Handles the dominator trees (dominator/post-dominator), and the
      computation of the dominance/post-dominance frontier.
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.doms = {}  # map of note to its dominator
        self.pdoms = {} # map of node to its post-dominator
        self.df = {}    # dominator frontier
        self.build()


    def build(self):
        graph = self.cfg.graph
        entry = self.cfg.entry_node
        self.build_dominators(graph, entry)
        entry = self.cfg.exit_node
        self.build_dominators(graph, entry, post_dom=True)


    def build_dominators(self, graph, entry, post_dom=False):
        """
          Builds the dominator tree based on:
            http://www.cs.rice.edu/~keith/Embed/dom.pdf

          Also used to build the post-dominator tree.
        """
        doms = self.doms if not post_dom else self.pdoms
        doms[entry] = entry
        post_order = dfs_postorder_nodes(graph, entry, post_dom)

        post_order_number = {}
        for i, n in enumerate(post_order):
            post_order_number[n] = i

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
                    pass
                while po_finger2 < po_finger1:
                    finger2 = doms.get(finger2, None)
                    po_finger2 = post_order_number[finger2]
                    if finger2 is None:
                        no_solution = True
                        break
                    pass
                if no_solution:
                    break

            return finger1

        changed = True

        while changed:
            changed = False
            for b in reversed(post_order):

                # Skip start node which doesn't have a predecessor
                # and was initialized above.
                if b == entry:
                    continue

                new_idom = None
                # Find a processed predecessor
                if post_dom:
                    predecessors = list(b.successors)
                else:
                    predecessors = [p for p in b.predecessors
                                    if post_order_number.get(p, -1) > post_order_number[b]]
                if len(predecessors) == 0:
                    continue

                new_idom = next(iter(predecessors))
                for p in predecessors:
                    if p == new_idom:
                        continue
                    if p in doms:
                        new_idom = intersec(p, new_idom)
                        pass
                    pass

                if b not in doms or doms[b] != new_idom:
                    doms[b] = new_idom
                    changed = True
                    pass
                pass
            pass
        return

    def tree(self, do_pdoms=False):
        """Makes a the dominator tree"""
        t_nodes = {}

        if do_pdoms:
            edge_type = 'pdom-edge'
            doms = self.pdoms
        else:
            edge_type = 'dom-edge'
            doms = self.doms

        t = TreeGraph()

        for node in doms:
            if node not in t_nodes:
                cur_node = t.make_add_node(node)
                t_nodes[node] = cur_node
            cur_node = t_nodes[node]

            parent = doms.get(node, None)
            if parent is not None and parent != node:
                if parent not in t_nodes:
                    parent_node = t.make_add_node(parent)
                    t_nodes[parent] = parent_node
                parent_node = t_nodes[parent]
                t.make_add_edge(parent_node, cur_node, edge_type)
                pass
            pass
        return t

def build_dom_set(t):
    """Makes a the dominator set for each node in the tree"""
    if t.nodes:
            return build_dom_set1(t.nodes[0])

def build_dom_set1(node):
    """Build dominator sets from dominator node"""

    node.bb.dom_set = set(node.bb.doms)
    for child in node.children:
        build_dom_set1(child)
        node.bb.dom_set |= child.bb.dom_set

# Note: this has to be done after calling tree
def dfs_forest(t):
    """
    Builds data flow graph using Depth-First search.
    """

    def dfs(seen, node):
        if node in seen:
            return
        seen.add(node)
        node.bb.doms = node.doms = set([node])
        node.bb.reach_offset = node.reach_offset = node.bb.end_offset
        for n in node.children:
            dfs(seen, n)
            node.doms |= node.doms
            node.bb.doms |= node.doms
            if node.reach_offset < n.reach_offset:
                node.bb.reach_offset = node.reach_offset = n.reach_offset
        # print("node %d has children %s" %
        #       (node.number, [n.number for n in node.children]))

    seen = set([])
    for node in t.nodes:
        if node not in seen:
            dfs(seen, node)
    return

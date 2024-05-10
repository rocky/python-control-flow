# -*- coding: utf-8 -*-
# Copyright (c) 2021, 2023, 2024 by Rocky Bernstein <rb@dustyfeet.com>
"""
  Dominator tree

  Copyright (c) 2017-2018, 2021, 2023-2024 by Rocky Bernstein
  Copyright (c) 2014 by Romain Gaucher (@rgaucher)
"""

from control_flow.bb import BasicBlock
from control_flow.graph import TreeGraph
from control_flow.traversals import dfs_postorder_nodes


class DominatorSet(set):
    def __str__(self) -> str:
        sorted_set = {dom.bb.number for dom in sorted(self)}
        return f"DominatorSet<{sorted_set}>"


class DominatorTree:
    """
    Handles the dominator trees (dominator/post-dominator), and the
    computation of the dominance/post-dominance frontier.
    """

    def __init__(self, cfg, debug=False):
        self.cfg = cfg
        self.debug = debug
        self.root = cfg.entry_node
        self.build()

    def build(self):
        graph = self.cfg.graph
        entry = self.cfg.entry_node

        self.doms = {}  # map of node to its dominator
        self.df = {}  # dominator frontier

        self.build_dominators(graph, entry)

        self.pdoms = {}  # map of node to its post-dominator
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
            # FIXME: if finger2 isn't in post_order_number, why not?
            if finger2 in post_order_number:
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
                        try:
                            po_finger2 = post_order_number[finger2]
                        except Exception:
                            no_solution = True
                            break
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
            order = post_order if reversed(post_order) else post_order
            for b in order:
                # Skip start node which doesn't have a predecessor
                # and was initialized above.
                if b == entry:
                    continue

                new_idom = None
                # Find a processed predecessor.
                # We want to order predecessors by closeness to
                # "b" the node we are computing a dominator from.
                # For dominators this is the number that is closest
                # and less than b.number.
                # For post dominators  it is the number that is closest
                # and greater than b.number.
                # Sorting also gives deterministic results.
                if post_dom:
                    n = len(b.predecessors)
                    predecessors = sorted(
                        [
                            p
                            for p in b.predecessors
                            if post_order_number.get(p, n) < post_order_number[b]
                        ],
                        key=lambda p: p.number,
                        reverse=False,
                    )
                else:
                    predecessors = sorted(
                        [
                            p
                            for p in b.predecessors
                            if post_order_number.get(p, -1) > post_order_number[b]
                        ],
                        key=lambda p: p.number,
                        reverse=True,
                    )

                # If no predecessors, then nothing to do here.
                if len(predecessors) == 0:
                    continue

                new_idom = next(iter(predecessors))
                for p in predecessors:
                    if p == new_idom:
                        continue
                    if p in doms:
                        new_idom = intersec(p, new_idom)
                        if new_idom is not None:
                            # We found the closest predecessor
                            break
                    pass

                if b not in doms or doms[b] != new_idom:
                    if b in doms:
                        b_number = doms[b].number
                        new_idom_number = new_idom.number
                        do_update = (
                            new_idom_number > b_number
                            if post_dom
                            else b_number > new_idom_number
                        )
                    else:
                        do_update = True
                    if do_update:
                        if self.debug:
                            name = "reverse dominator" if post_dom else "dominator"
                            print(
                              f"{name}[{b.number}] is "
                                "{None if new_idom is None else new_idom.number}"
                            )

                        doms[b] = new_idom
                        changed = True
                        pass
                    pass
                pass
            pass
        return

    def tree(self, do_pdoms=False):
        """Makes the dominator tree"""
        t_nodes = {}

        # We sort dominators to give deterministic results.
        if do_pdoms:
            edge_type = "pdom-edge"
            doms_list = sorted(self.pdoms, key=lambda x: x.number, reverse=False)
            doms = self.pdoms
        else:
            edge_type = "dom-edge"
            doms_list = sorted(self.doms, key=lambda x: x.number, reverse=True)
            doms = self.doms

        root = self.cfg.entry_node if do_pdoms else self.cfg.exit_node
        t = TreeGraph(root)

        for node in doms_list:
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

    def offset_dominates(self, start_offset: int) -> bool:
        cfg = self.cfg
        start_block = cfg.get_block(start_offset)
        end_block = cfg.get_block(start_offset)
        # FIXME: is this right
        return start_block in end_block.doms


def build_dom_set(t, do_pdoms, debug=False):
    """Makes the dominator set for each node in the tree"""
    seen = DominatorSet()
    for node in t.nodes:
        if node not in seen:
            seen.add(node)
            build_dom_set1(node, do_pdoms, debug)
            pass
        pass


def build_dom_set1(node, do_pdoms, debug=False):
    """Build dominator sets from dominator node"""

    if do_pdoms:
        node.bb.pdom_set = DominatorSet(node.bb.pdoms)
    else:
        node.bb.dom_set = DominatorSet(node.bb.doms)
        pass

    for child in node.children:
        build_dom_set1(child, do_pdoms, debug)
        if do_pdoms:
            node.bb.pdom_set |= child.bb.pdom_set
        else:
            node.bb.dom_set |= child.bb.dom_set


# Note: this has to be done after calling tree()
# which builds the dominator tree.
def dfs_forest(t, do_pdoms):
    """
    Builds data flow graph using Depth-First search.
    """

    def dfs(seen, node, do_pdoms):
        if node in seen:
            return
        seen.add(node)
        if do_pdoms:
            node.bb.pdoms = node.pdoms = DominatorSet([node])
        else:
            node.bb.doms = node.doms = DominatorSet([node])
            node.bb.reach_offset = node.reach_offset = node.bb.end_offset
            # print(f"XXX1: {node.bb} reach_offset set to {node.bb.end_offset}")

        for n in node.children:
            dfs(seen, n, do_pdoms)
            if do_pdoms:
                node.pdoms |= n.pdoms
                node.bb.pdoms |= node.pdoms
            else:
                node.doms |= n.doms
                node.bb.doms |= node.doms
                if node.reach_offset < n.reach_offset:
                    # print(f"XXX1: {node.bb} reach_offset set to {n.reach_offset}")
                    node.bb.reach_offset = node.reach_offset = n.reach_offset
                    pass
                pass
        # print("node %d has children %s" %
        #       (node.number, [n.number for n in node.children]))

    seen = set([])
    for node in t.nodes:
        if node not in seen:
            dfs(seen, node, do_pdoms)
    return


def dominates(bb1: BasicBlock, bb2: BasicBlock) -> bool:
    """Return true if bb1 dominates bb2. In other words,
    bb2 is in bb1's dominator set.
    """
    return bb2 in bb1.dom_set

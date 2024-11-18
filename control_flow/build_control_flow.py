# Copyright (c) 2021-2024 by Rocky Bernstein <rb@dustyfeet.com>

import sys
from xdis.codetype.base import iscode
from xdis.op_imports import get_opcode_module
from xdis.version_info import IS_PYPY, PYTHON_VERSION_TRIPLE

from control_flow.augment_disasm import augment_instructions
from control_flow.bb import BB_JUMP_UNCONDITIONAL, BB_NOFOLLOW, basic_blocks
from control_flow.cfg import ControlFlowGraph
from control_flow.dominators import DominatorTree
from control_flow.graph import BB_DEAD_CODE, write_dot

VARIANT = "pypy" if IS_PYPY else None


def build_and_analyze_control_flow(
    func_or_code,
    graph_options: str = "",
    opc=None,
    code_version_tuple=PYTHON_VERSION_TRIPLE[:2],
    func_or_code_timestamp=None,
    func_or_code_name: str = "",
    debug: dict = {},
    file_part: str = "",
):
    """
    Compute control-flow graph, dominator information, and
    assembly instructions augmented with control flow for
    function "func".
    """

    debug_dict: dict = {}
    if graph_options in {"all", "dom"}:
        debug_dict["dom"] = True

    if iscode(func_or_code):
        code = func_or_code
    else:
        code = func_or_code.__code__
        if func_or_code_name == "":
            func_or_code_name = func_or_code.__name__
    if func_or_code_name.startswith("<"):
        func_or_code_name = func_or_code_name[1:]
    if func_or_code_name.endswith(">"):
        func_or_code_name = func_or_code_name[:-1]

    # print(func_or_code_name)

    # disco(code_version_tuple, code, func_or_code_timestamp)

    if opc is None:
        opc = get_opcode_module(code_version_tuple, VARIANT)

    offset2inst_index = {}
    linestarts = dict(opc.findlinestarts(code, dup_lines=True))
    bb_mgr = basic_blocks(code, linestarts, offset2inst_index, code_version_tuple)

    # for bb in bb_mgr.bb_list:
    #     print("\t", bb)

    cfg = ControlFlowGraph(bb_mgr)
    assert cfg.graph is not None, "Failed to build graph"

    version = ".".join((str(n) for n in code_version_tuple[:2]))
    if graph_options in ("all", "control-flow"):
        write_dot(
            f"{file_part}{func_or_code_name}",
            f"/tmp/flow-{version}-",
            cfg.graph,
            write_png=True,
            exit_node=cfg.exit_node,
        )

    assert cfg.graph is not None
    try:
        cfg.dom_tree = DominatorTree.compute_dominators_in_cfg(cfg, debug_dict.get("dom", False))
        for node in cfg.graph.nodes:
            if node.bb.nesting_depth < 0:
                node.is_dead_code = True
                node.bb.flags.add(BB_DEAD_CODE)
            else:
                node.is_dead_code = False

        classify_join_nodes_and_edges(cfg)

        if graph_options in ("all", "dominators"):
            write_dot(
                f"{file_part}{func_or_code_name}",
                f"/tmp/flow-dom-{version}-",
                cfg.dom_forest,
                write_png=True,
                exit_node=cfg.exit_node,
            )

        cfg.classify_edges()
        if graph_options in ("all",):
            write_dot(
                f"{file_part}{func_or_code_name}",
                f"/tmp/flow+dom-{version}-",
                cfg.graph,
                write_png=True,
                is_dominator_format=True,
                exit_node=cfg.exit_node,
            )

        assert cfg.graph

        augmented_instrs = augment_instructions(
            func_or_code, cfg, opc, offset2inst_index, bb_mgr
        )
        if graph_options in ("all", "augmented-instructions"):
            print("=" * 30)
            print("Augmented Instructions:")
            for inst in augmented_instrs:
                print(inst.disassemble(opc))

        # return cs_str
    except Exception:
        import traceback

        traceback.print_exc()
        print("Unexpected error:", sys.exc_info()[0])
        print(f"{func_or_code_name} had an error")
        return cfg, []
    return cfg, augmented_instrs


def classify_join_nodes_and_edges(cfg: ControlFlowGraph):
    """
    Classify basic blocks as whether the first instruction
    is a join instructions, also mark join edges.
    """
    assert cfg.graph is not None, "Graph should have been previously set"
    cfg.graph.add_edge_info_to_nodes()
    assert cfg.graph is not None
    for node in cfg.graph.nodes:
        node_nesting_depth = node.bb.nesting_depth
        if node.is_dead_code:
            node_nesting_depth = 0
        else:
            assert node.bb.nesting_depth >= 0
        for edge in node.in_edges:
            if edge.source.is_dead_code:
                source_nesting_depth = 0
            else:
                source_nesting_depth = edge.source.bb.nesting_depth
                assert source_nesting_depth >= 0
            if (
                source_nesting_depth >= node_nesting_depth
                and edge.kind
                not in (
                    "self-loop",
                    "looping",
                )
                and not (edge.source.flags & {BB_NOFOLLOW, BB_JUMP_UNCONDITIONAL})
            ):
                node.is_join_node = True
                edge.is_join = True
        if node.is_join_node is not True:
            assert node.is_join_node is None
            node.is_join_node = False

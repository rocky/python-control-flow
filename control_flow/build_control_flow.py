# Copyright (c) 2021-2024 by Rocky Bernstein <rb@dustyfeet.com>

from xdis.codetype.base import iscode
from xdis.disasm import disco
from xdis.op_imports import get_opcode_module
from xdis.version_info import IS_PYPY, PYTHON_VERSION_TRIPLE

from control_flow.augment_disasm import augment_instructions
from control_flow.bb import basic_blocks
from control_flow.cfg import ControlFlowGraph
from control_flow.dominators import DominatorTree, build_dom_set, dfs_forest
from control_flow.graph import write_dot

VARIANT = "pypy" if IS_PYPY else None

def build_and_analyze_control_flow(
    func_or_code,
    graph_options: str = "",
    opc=None,
    code_version_tuple=PYTHON_VERSION_TRIPLE[:2],
    func_or_code_timestamp=None,
    func_or_code_name: str = "",
    debug: dict = {},
):
    """
    Compute control-flow graph, dominator information, and
    assembly instructions augmented with control flow for
    function "func".
    """

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

    print(func_or_code_name)

    disco(code_version_tuple, code, func_or_code_timestamp)

    if opc is None:
        opc = get_opcode_module(code_version_tuple, VARIANT)

    offset2inst_index = {}
    bb_mgr = basic_blocks(code, offset2inst_index, code_version_tuple)

    # for bb in bb_mgr.bb_list:
    #     print("\t", bb)

    cfg = ControlFlowGraph(bb_mgr)
    assert cfg.graph is not None, "Failed to build graph"

    version = ".".join((str(n) for n in code_version_tuple[:2]))
    if graph_options in ("all", "control-flow"):
        write_dot(
            func_or_code_name,
            f"/tmp/flow-{version}-",
            cfg.graph,
            write_png=True,
            exit_node=cfg.exit_node,
        )

    try:
        dt = DominatorTree(cfg, debug.get("dom", False))

        cfg.dom_tree = dt.build_dom_tree()
        dfs_forest(cfg.dom_tree)
        cfg.graph.max_nesting = cfg.max_nesting_depth = cfg.dom_tree.max_nesting
        build_dom_set(cfg.dom_tree, debug.get("dom", False))

        # FIXME
        # classify "join" nodes and edges

        if graph_options in ("all", "dominators"):
            write_dot(
                func_or_code_name,
                f"/tmp/flow-dom-{version}-",
                cfg.dom_tree,
                write_png=True,
                exit_node=cfg.exit_node,
            )

        if graph_options in ("all",):
            write_dot(
                func_or_code_name,
                f"/tmp/flow+dom-{version}-",
                cfg.graph,
                write_png=True,
                is_dominator_format=True,
                exit_node=cfg.exit_node,
            )

        assert cfg.graph

        print("=" * 30)
        augmented_instrs = augment_instructions(
            func_or_code, cfg, opc, offset2inst_index, bb_mgr
        )
        for inst in augmented_instrs:
            print(inst.disassemble(opc))

        # return cs_str
    except Exception:
        import traceback

        traceback.print_exc()
        print("Unexpected error:", sys.exc_info()[0])
        print(f"{func_or_code_name} had an error")

def classify_join_nodes_and_edges(cfg: ControlFlowGraph):
    """
    Classify basic blocks as whether the first instruction
    is a join instructions, also mark join edges.
    """
    assert cfg
    return

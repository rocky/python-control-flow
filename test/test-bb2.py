#!/usr/bin/env python
import sys
import os
import os.path as osp
from control_flow.build_control_flow import build_and_analyze_control_flow
from types import CodeType
from xdis.load import check_object_path, load_module
from xdis.version_info import PYTHON_VERSION_TRIPLE


def testing():
    assert False, (
        "This should have been replaced via read-in python script with a function "
        "called testing"
    )


if len(sys.argv) == 1:
    print("You need to give a file func_or_code_name")
    sys.exit(1)
    pass

filename = sys.argv[1]
short = ""
stat = os.stat(filename)
if filename.endswith(".py"):
    exec(open(filename).read())
    short = osp.basename(filename)[0:-3]
    source = open(filename, "r").read()
    co = compile(source, filename, "exec")
    timestamp = stat.st_mtime
    version_tuple = PYTHON_VERSION_TRIPLE

    name = co.co_name
    if name.startswith("<"):
        name = name[1:]
    if name.endswith(">"):
        name = name[:-1]

elif filename.endswith(".pyc"):
    timestamp = stat.st_mtime
    short = osp.basename(filename)[0:-4]
    pyc_filename = check_object_path(filename)
    (
        version_tuple,
        timestamp,
        _,  # magic_int,
        co,
        _,  # is_pypy,
        _,  # source_size,
        _,  # sip_hash,
    ) = load_module(pyc_filename)

func_name="<module>"
if len(sys.argv) == 3:
    func_name = sys.argv[2]
    func_codes = [const for const in co.co_consts if isinstance(const, CodeType) and const.co_name == func_name]
    len_func_codes = len(func_codes)
    if len_func_codes == 0:
        print(f"Did not find a code object named {func_name}")
        sys.exit(1)
    elif len_func_codes == 1:
        co = func_codes[0]
    elif len_func_codes > 1:
        print(f"Found too many code objects named {func_name}:\n{func_codes}")
        sys.exit(1)


build_and_analyze_control_flow(
    co,
    graph_options="all",
    code_version_tuple=version_tuple,
    func_or_code_timestamp=timestamp,
    func_or_code_name=func_name,
    debug={},
    file_part=f"{short}-"
)

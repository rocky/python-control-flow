#!/usr/bin/env python
# Copyright (c) 2021-2024 by Rocky Bernstein <rb@dustyfeet.com>

import click
import importlib
import os
import os.path as osp
import sys

from xdis.load import check_object_path, load_module
from xdis.version_info import PYTHON_VERSION_TRIPLE

from python_control_flow.build_control_flow import build_and_analyze_control_flow
from python_control_flow.version import __version__

@click.command()
@click.version_option(version=__version__)
@click.option(
    "-i", "--import", "import_name", help="function, or class inside the module name"
)
@click.option("-m", "--member", help="function, or class inside the module name")
@click.option("--filename", "-f", type=click.Path(readable=True))
@click.option(
    "--graph",
    "-g",
    type=click.Choice(
        ["all", "control-flow", "dominators", "none"],
        case_sensitive=False,
    ),
    default="none",
    help="Produce graphviz graph of program",
)
def main(import_name, member, filename, graph):
    try:
        if import_name is not None:
            import_module = importlib.__import__(import_name)
            if member is not None:
                if hasattr(import_module, member):
                    co = getattr(import_module, member).__code__
                    timestamp = None
                    version_tuple = PYTHON_VERSION_TRIPLE
                else:
                    print(f"module {import_name} has no member {member}")
                    sys.exit(1)
            else:
                import_filename = import_module.__file__
                if filename is not None and import_filename != filename:
                    print(
                        f"--filename and --import but files do not match: {filename} vs. {import_filename}"
                    )
                    print("Use just one option")
                    sys.exit(1)
                filename = import_filename

        if filename is not None:
            # FIXME: add whether we want PyPy
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
            filename = pyc_filename
        else:
            print("either options --filename or --import must be given")
            sys.exit(2)

    except Exception:
        # Hack alert: we're using pyc_filename set as a proxy for whether the filename
        # exists.
        # check_object_path() will succeed if the file exists.
        if filename is not None:
            stat = os.stat(filename)
            source = open(filename, "r").read()
            co = compile(source, filename, "exec")
            timestamp = stat.st_mtime
            version_tuple = PYTHON_VERSION_TRIPLE
        else:
            print("Some sort of error involving filename")
            sys.exit(1)

    name = co.co_name
    if name == "<module>":
        name = osp.basename(co.co_filename)
    if name.startswith("<"):
        name = name[1:]
    if name.endswith(">"):
        name = name[:-1]

    build_and_analyze_control_flow(
        co,
        graph_options=graph,
        code_version_tuple=version_tuple,
        func_or_code_timestamp=timestamp,
        func_or_code_name=name,
    )


if __name__ == "__main__":
    main(sys.argv[1:])

#!/usr/bin/env python3

import argparse
from pathlib import Path
import resource
import tempfile

from configs import CONFIGS
from compile import compile

def absolute_path(x):
    return str(Path(x).resolve())

def create_run_dir():
    # Depending on the answer to our email, we might change this to use cwd, or to use /tmp as base
    #return tempfile.TemporaryDirectory(prefix="run_dir_", dir=Path(".").resolve())
    return tempfile.mkdtemp(prefix="run_dir_", dir=Path(".").resolve())


def run_config(config, memory_limit, time_limit, col_filename, dat_filename):
    run_dir = create_run_dir()
    sas_filename = str(Path(run_dir) / "problem.sas")
    compile("split", col_filename, dat_filename, sas_filename)
    response = config.run(run_dir, memory_limit, time_limit, col_filename, dat_filename, sas_filename)
    # Either print output to stdout or write to file, we don't know.
    if response is not None:
        print(response)
    else:
        print("c UNKNOWN")


def parse_options():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", choices=CONFIGS.keys(), required=True)
    parser.add_argument("--memory-limit", type=int)
    parser.add_argument("--time-limit", type=int)
    parser.add_argument("col_filename", type=absolute_path)
    parser.add_argument("dat_filename", type=absolute_path)
    return parser.parse_args()


def main():
    args = parse_options()
    config = CONFIGS[args.config]

    memory_limit = args.memory_limit
    if memory_limit is None:
        memory_limit, _ = resource.getrlimit(resource.RLIMIT_AS)
    else:
        memory_limit = memory_limit * 1024 * 1024 * 1024 # limit is given in GB, we need it in bytes

    time_limit = args.time_limit
    if time_limit is None:
        time_limit, _ = resource.getrlimit(resource.RLIMIT_CPU)

    run_config(config, memory_limit, time_limit, args.col_filename, args.dat_filename)


if __name__ == "__main__":
    main()

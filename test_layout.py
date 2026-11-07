"""
Sanity-checks the compiler's layouts: for each case in tests/NAME.json (a SHARD_AMT and a GRID for the test's program),
compiles the program afresh with the compiler placing its rules, into out/tests/NAME/, and asks the program's
layout_reasonable about the layout. Prints each case's verdict, and exits nonzero if any layout is unreasonable or any
case didn't compile.

    python test_layout.py tests/NAME.json
"""
import json
import os
import sys

from compile import compile_program, grid_nodes
from programs import PROGRAMS
from run import OUT


def main():
    path = sys.argv[1]
    test = json.load(open(path))
    program = test["program"]
    out = os.path.join(OUT, "tests", os.path.splitext(os.path.basename(path))[0])
    failed = False
    for case in test["cases"]:
        shard_amt, grid = case["shard_amt"], case["grid"]
        name = f"{program}, {shard_amt} shards on {grid}"
        try:
            prog_dir = compile_program(program, shard_amt, "compiler", grid, os.path.join(out, f"{program}-{shard_amt}-{grid}"))
        except RuntimeError as e:
            print(f"{name}: didn't compile: {str(e).strip().splitlines()[-1]}", flush=True)
            failed = True
            continue
        on = {tuple(node): rules for node, rules in json.load(open(os.path.join(prog_dir, "layout.json")))["layout"]}
        # one entry for every node of the grid, so a node the compiler left empty counts
        rule_sets = [on.get(tuple(node), []) for node in grid_nodes(grid)]
        if PROGRAMS[program].layout_reasonable(shard_amt, rule_sets):
            print(f"{name}: ok", flush=True)
        else:
            layout = ", ".join(f"({x},{y}): {sorted(rules)}" for (x, y), rules in zip(grid_nodes(grid), rule_sets))
            print(f"{name}: UNREASONABLE: {layout}", flush=True)
            failed = True
    sys.exit(failed)


if __name__ == "__main__":
    main()

"""
Compiles programs/PROGRAM with SHARD_AMT shards for a GRID, its rules placed by PLACEMENT (ideal: the layout its rules
suggest, node k being the k-th of the grid's nodes in (x, y) order; single: every rule on (0,0); compiler: the
compiler's optimizer), into OUT_DIR: the program as prog.dl, the layout or locations given to the compiler, and the
compiled program in OUT_DIR/prog. Input facts enter, and outputs are collected, at (0,0). DATALOG_COMPILER names the
distributing-datalog-compiler checkout to use.

    python compile.py PROGRAM SHARD_AMT PLACEMENT GRID OUT_DIR
    e.g. python compile.py bfs 4 compiler 2x2 out/bfs
"""
import json
import os
import shutil
import subprocess
import sys

from programs import PROGRAMS

PLACEMENTS = ("ideal", "single", "compiler")


def checkout(var, repo):
    path = os.environ.get(var)
    if not path:
        sys.exit(f"set {var} to your {repo} checkout")
    return path


def grid_nodes(grid):
    w, h = map(int, grid.split("x"))
    return [[x, y] for x in range(w) for y in range(h)]


def dl(relations, rules):
    """The program as a .dl: its declarations, then its rules."""
    decls = [f".decl {rel}({', '.join(f'{v}: number' for v in 'xyzwuv'[:arity])})" for rel, arity in relations.items()]
    return "\n".join(decls + [""] + [rule for _, rule in rules]) + "\n"


def compile_program(program, shard_amt, placement, grid, out_dir):
    """The compiled program's directory, out_dir/prog, compiled afresh."""
    if placement not in PLACEMENTS:
        raise ValueError(f"placement must be one of {', '.join(PLACEMENTS)}, not {placement!r}")
    os.makedirs(out_dir, exist_ok=True)
    prog_dir = os.path.join(out_dir, "prog")
    shutil.rmtree(prog_dir, ignore_errors=True)
    prog = PROGRAMS[program]
    rules = prog.rules(shard_amt)
    with open(os.path.join(out_dir, "prog.dl"), "w") as f:
        f.write(dl(prog.relations(shard_amt), rules))

    layout = {"fact_producers": {rel: [[0, 0]] for rel in prog.input_relations(shard_amt)},
              "fact_consumers": {rel: [[0, 0]] for rel in prog.output_relations(shard_amt)}}
    if placement != "compiler":
        nodes, on = grid_nodes(grid), {}
        for k, (node, _) in enumerate(rules):
            on.setdefault(tuple(nodes[node if placement == "ideal" else 0]), []).append(k)
        layout["layout"] = [[list(node), ks] for node, ks in on.items()]
    flag, path = ("--locations", "locations.json") if placement == "compiler" else ("--layout", "layout.json")
    with open(os.path.join(out_dir, path), "w") as f:
        json.dump(layout, f)

    ddc = checkout("DATALOG_COMPILER", "distributing-datalog-compiler")
    w, h = grid.split("x")
    p = subprocess.run([os.path.join(ddc, ".venv", "bin", "python3"), os.path.join(ddc, "src", "auto-compiler", "simple_compile.py"),
                        os.path.join(out_dir, "prog.dl"), "--dims", w, h, flag, os.path.join(out_dir, path), "-o", prog_dir],
                       capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f"the compiler failed: {(p.stderr or p.stdout).strip()}")
    return prog_dir


if __name__ == "__main__":
    program, shard_amt, placement, grid, out_dir = sys.argv[1:]
    print(compile_program(program, int(shard_amt), placement, grid, out_dir))

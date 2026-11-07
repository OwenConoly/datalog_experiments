"""
One run: programs/PROGRAM with SHARD_AMT shards, its rules placed on a GRID by PLACEMENT (see compile.py), simulated at
L2 on datasets/DATASET's SIZE and SEED sharded by the program's SHARDER, and checked by the program's
check_correctness. Input facts enter, and outputs are collected, at (0,0).

    python run.py PROGRAM SHARD_AMT SHARDER PLACEMENT GRID DATASET SIZE SEED
    e.g. python run.py bfs 4 metis ideal 2x2 oldenburg 500 0

Compiled programs go in out/compiled/, compiled once and reused after; runs go in out/runs/. DATALOG_COMPILER and
DATALOG_SIMULATOR name the distributing-datalog-compiler and distributed-datalog-simulator checkouts to use.
"""
import json
import os
import subprocess
import sys

from compile import checkout, compile_program
from datasets import DATASETS
from programs import PROGRAMS

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def compiled(program, shard_amt, placement, grid):
    """The compiled program's directory, compiled the first time it's asked for."""
    d = os.path.join(OUT, "compiled", f"{program}-{shard_amt}-{placement}-{grid}")
    if os.path.exists(os.path.join(d, "prog", "nodes.json")):
        return os.path.join(d, "prog")
    return compile_program(program, shard_amt, placement, grid, d)


def hw_config(grid, prog_dir):
    """The grid's configuration, next to the compiled program: max_tries and max_rules raised to fit it (both change
    timing a little), and the per-round delta and per-node EDB buffers raised (checks only)."""
    sim = checkout("DATALOG_SIMULATOR", "distributed-datalog-simulator")
    config = json.load(open(os.path.join(sim, "hw-configs", f"grid{grid}.json")))
    while config["evaluator"]["max_tries"] < len(json.load(open(os.path.join(prog_dir, "relids.json")))):
        config["evaluator"]["max_tries"] *= 2
    while config["evaluator"]["max_rules"] < max(len(n["program"]) for n in json.load(open(os.path.join(prog_dir, "nodes.json")))):
        config["evaluator"]["max_rules"] *= 2
    config["updater"]["max_delta_per_round"] = 10**9
    config["updater"]["delta_chunks"] = 100_000
    config["boot"]["max_edb_facts_per_node"] = 10**6
    path = os.path.join(os.path.dirname(prog_dir), "hw_config.json")
    with open(path, "w") as f:
        json.dump(config, f, indent=2)
    return path


def run(program, shard_amt, sharder, placement, grid, dataset, size, seed):
    prog_dir = compiled(program, shard_amt, placement, grid)
    config = hw_config(grid, prog_dir)
    prog, data = PROGRAMS[program], DATASETS[dataset].generate(size, seed)

    d = os.path.join(OUT, "runs", f"{program}-{shard_amt}-{sharder}-{placement}-{grid}-{dataset}-{size}-{seed}")
    os.makedirs(d, exist_ok=True)
    facts, summary, answer = (os.path.join(d, f) for f in ("facts.json", "summary.json", "answer.json"))
    with open(facts, "w") as f:
        json.dump([{"rel": rel, "args": [str(a) for a in args], "node": [0, 0], "timestamp": 42}
                   for rel, args in prog.inputs(data, shard_amt, sharder)], f)
    sim = checkout("DATALOG_SIMULATOR", "distributed-datalog-simulator")
    subprocess.run(["cargo", "build", "--release", "-q", "--manifest-path", os.path.join(sim, "Cargo.toml")], check=True)
    p = subprocess.run([os.path.join(sim, "target", "release", "distributed-datalog-simulator"), "run", "--program", prog_dir, "--facts", facts, "--hw-config", config, "--quiet",
                        "--summary-json", summary, "--facts-json", answer], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f"the simulator failed: {p.stderr.strip()}")

    s = json.load(open(summary))
    wanted = set(prog.output_relations(shard_amt))
    outputs = {r["name"]: [tuple(f) for f in r["facts"]] for r in json.load(open(answer))["relations"] if r["name"] in wanted}
    return {"evaluation": s["cycles"]["evaluation"], "boot": s["cycles"]["boot"],
            "rounds": max(n["rounds"] for n in s["nodes"]), "correct": prog.check_correctness(data, outputs)}


if __name__ == "__main__":
    program, shard_amt, sharder, placement, grid, dataset, size, seed = sys.argv[1:]
    print(run(program, int(shard_amt), sharder, placement, grid, dataset, int(size), int(seed)))

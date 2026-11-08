"""
One run: programs/PROGRAM with SHARD_AMT shards, its rules placed on a GRID by PLACEMENT (see compile.py), simulated at
L2 on datasets/DATASET's SIZE and SEED sharded by the program's SHARDER, and checked by the program's
check_correctness. Input facts enter, and outputs are collected, at (0,0). Every run simulates the hardware described
by hw_config.json: the simulator's hw-configs/grid3x3.json, with room for 25 nodes and for 128 rules and 128 relations at
a node, enough for every program here, and with the per-round delta and per-node EDB buffers raised (checks only).

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


def compiled(program, shard_amt, placement, grid, out=OUT):
    """The compiled program's directory under out/compiled/, compiled the first time it's asked for."""
    d = os.path.join(out, "compiled", f"{program}-{shard_amt}-{placement}-{grid}")
    if os.path.exists(os.path.join(d, "prog", "nodes.json")):
        return os.path.join(d, "prog")
    return compile_program(program, shard_amt, placement, grid, d)


def run(program, shard_amt, sharder, placement, grid, dataset, size, seed, out=OUT):
    """The run's results; its program is compiled under out/compiled/ and its files go under out/runs/."""
    prog_dir = compiled(program, shard_amt, placement, grid, out)
    prog, data = PROGRAMS[program], DATASETS[dataset].generate(size, seed)

    d = os.path.join(out, "runs", f"{program}-{shard_amt}-{sharder}-{placement}-{grid}-{dataset}-{size}-{seed}")
    os.makedirs(d, exist_ok=True)
    facts, summary, answer = (os.path.join(d, f) for f in ("facts.json", "summary.json", "answer.json"))
    with open(facts, "w") as f:
        json.dump([{"rel": rel, "args": [str(a) for a in args], "node": [0, 0], "timestamp": 42}
                   for rel, args in prog.inputs(data, shard_amt, sharder)], f)
    sim = checkout("DATALOG_SIMULATOR", "distributed-datalog-simulator")
    subprocess.run(["cargo", "build", "--release", "-q", "--manifest-path", os.path.join(sim, "Cargo.toml")], check=True)
    p = subprocess.run([os.path.join(sim, "target", "release", "distributed-datalog-simulator"), "run", "--program", prog_dir, "--facts", facts, "--hw-config", os.path.join(HERE, "hw_config.json"), "--quiet",
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

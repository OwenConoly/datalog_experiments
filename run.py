"""
One run: programs/PROGRAM with SHARD_AMT shards, its rules placed on a GRID by PLACEMENT (ideal: the layout its
rules suggest, node k being the k-th of the grid's nodes in (x, y) order; single: every rule on (0,0); compiler: the
compiler's optimizer), simulated at L2 on datasets/DATASET's SIZE and SEED sharded by its io.py's SHARDER, and checked
by its io.py's check_correctness. Input facts enter, and outputs are collected, at (0,0).

    python run.py PROGRAM SHARD_AMT SHARDER PLACEMENT GRID DATASET SIZE SEED
    e.g. python run.py bfs 4 metis ideal 2x2 oldenburg 500 0

Compiled programs go in out/compiled/, runs in out/runs/. DATALOG_COMPILER and DATALOG_SIMULATOR name the
distributing-datalog-compiler and distributed-datalog-simulator checkouts to use.
"""
import importlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def checkout(var, repo):
    path = os.environ.get(var)
    if not path:
        sys.exit(f"run.py: set {var} to your {repo} checkout")
    return path


def grid_nodes(grid):
    w, h = map(int, grid.split("x"))
    return [[x, y] for x in range(w) for y in range(h)]


def compile_program(program, shard_amt, placement, grid):
    """The compiled program's directory (compiled once), and its hardware configuration's path."""
    d = os.path.join(OUT, "compiled", f"{program}-{shard_amt}-{placement}-{grid}")
    config_path = os.path.join(d, "hw_config.json")
    if os.path.exists(config_path):
        return os.path.join(d, "prog"), config_path
    os.makedirs(d, exist_ok=True)
    prog = importlib.import_module(f"programs.{program}.program")
    io = importlib.import_module(f"programs.{program}.io")
    relations, rules = prog.relations(shard_amt), prog.rules(shard_amt)

    with open(os.path.join(d, "prog.dl"), "w") as f:
        for rel, arity in relations.items():
            f.write(f".decl {rel}({', '.join(f'{v}: number' for v in 'xyzwuv'[:arity])})\n")
        f.write("\n")
        for _, rule in rules:
            f.write(rule + "\n")

    locations = {"fact_producers": {rel: [[0, 0]] for rel in io.input_relations(shard_amt)},
                 "fact_consumers": {rel: [[0, 0]] for rel in io.output_relations(shard_amt)}}
    nodes = grid_nodes(grid)
    if placement == "compiler":
        where = ["--locations", os.path.join(d, "locations.json")]
        layout = locations
    else:
        on = {}
        for k, (node, _) in enumerate(rules):
            on.setdefault(tuple(nodes[node] if placement == "ideal" else nodes[0]), []).append(k)
        where = ["--layout", os.path.join(d, "layout.json")]
        layout = {"layout": [[list(node), ks] for node, ks in on.items()], **locations}
    with open(where[1], "w") as f:
        json.dump(layout, f)
    w, h = grid.split("x")
    ddc = checkout("DATALOG_COMPILER", "distributing-datalog-compiler")
    p = subprocess.run([os.path.join(ddc, ".venv", "bin", "python3"), os.path.join(ddc, "src", "auto-compiler", "simple_compile.py"),
                        os.path.join(d, "prog.dl"), "--dims", w, h, *where, "-o", os.path.join(d, "prog")],
                       capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f"the compiler failed: {(p.stderr or p.stdout).strip()}")

    # The grid's configuration, with max_tries and max_rules raised to fit the program (both change timing a little)
    # and the per-round delta and per-node EDB buffers raised (checks only).
    sim = checkout("DATALOG_SIMULATOR", "distributed-datalog-simulator")
    config = json.load(open(os.path.join(sim, "hw-configs", f"grid{grid}.json")))
    while config["evaluator"]["max_tries"] < len(relations):
        config["evaluator"]["max_tries"] *= 2
    most = max(len(node["program"]) for node in json.load(open(os.path.join(d, "prog", "nodes.json"))))
    while config["evaluator"]["max_rules"] < most:
        config["evaluator"]["max_rules"] *= 2
    config["updater"]["max_delta_per_round"] = 10**9
    config["updater"]["delta_chunks"] = 100_000
    config["boot"]["max_edb_facts_per_node"] = 10**6
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    return os.path.join(d, "prog"), config_path


def run(program, shard_amt, sharder, placement, grid, dataset, size, seed):
    prog_dir, config = compile_program(program, shard_amt, placement, grid)
    io = importlib.import_module(f"programs.{program}.io")
    data = importlib.import_module(f"datasets.{dataset}.dataset").generate(size, seed)

    d = os.path.join(OUT, "runs", f"{program}-{shard_amt}-{sharder}-{placement}-{grid}-{dataset}-{size}-{seed}")
    os.makedirs(d, exist_ok=True)
    facts, summary, answer = (os.path.join(d, f) for f in ("facts.json", "summary.json", "answer.json"))
    with open(facts, "w") as f:
        json.dump([{"rel": rel, "args": [str(a) for a in args], "node": [0, 0], "timestamp": 42}
                   for rel, args in io.inputs(data, shard_amt, sharder)], f)
    sim = checkout("DATALOG_SIMULATOR", "distributed-datalog-simulator")
    subprocess.run(["cargo", "build", "--release", "-q", "--manifest-path", os.path.join(sim, "Cargo.toml")], check=True)
    p = subprocess.run([os.path.join(sim, "target", "release", "distributed-datalog-simulator"), "run", "--program", prog_dir, "--facts", facts, "--hw-config", config, "--quiet",
                        "--summary-json", summary, "--facts-json", answer], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f"the simulator failed: {p.stderr.strip()}")

    s = json.load(open(summary))
    wanted = set(io.output_relations(shard_amt))
    outputs = {r["name"]: [tuple(f) for f in r["facts"]] for r in json.load(open(answer))["relations"] if r["name"] in wanted}
    return {"evaluation": s["cycles"]["evaluation"], "boot": s["cycles"]["boot"],
            "rounds": max(n["rounds"] for n in s["nodes"]), "correct": io.check_correctness(data, outputs)}


if __name__ == "__main__":
    program, shard_amt, sharder, placement, grid, dataset, size, seed = sys.argv[1:]
    print(run(program, int(shard_amt), sharder, placement, grid, dataset, int(size), int(seed)))

"""
All-pairs paths (Path, the transitive closure) built from each shard's own closure and the closure of the boundary
between shards. Shard i's rules use E{i} (its edges), T{i} (their closure), B{i} (its ends of edges leaving it) and
Enters{i}; the boundary closure's rules (all_boundary, TC_boundary) go on a hub. The suggested layout puts the hub in the
middle of the smallest square grid with shard_amt + 1 nodes, and the shards on the other nodes in order. A dataset is a
graph (see graphs.py).
"""
import math

from ..graphs import closure, metis, mod


def relations(shard_amt):
    per_shard = {f"E{i}": 2 for i in range(shard_amt)} | {f"T{i}": 2 for i in range(shard_amt)} \
        | {f"B{i}": 1 for i in range(shard_amt)} | {f"Enters{i}": 2 for i in range(shard_amt)}
    return per_shard | {"Exits": 2, "inter_boundary": 2, "all_boundary": 2, "TC_boundary": 2, "Path": 2}


def rules(shard_amt):
    g = math.ceil(math.sqrt(shard_amt + 1))
    hub = (g - 1) // 2 * g + (g - 1) // 2
    node = [k for k in range(g * g) if k != hub]
    return [(node[i], rule) for i in range(shard_amt) for rule in (
        f"T{i}(x, y) :- E{i}(x, y).",
        f"T{i}(x, y) :- T{i}(x, z), E{i}(z, y).",
        f"all_boundary(x, y) :- T{i}(x, y), B{i}(x), B{i}(y).",
        f"Path(x, y) :- T{i}(x, y).",
        f"Exits(x, exit) :- T{i}(x, exit), B{i}(exit).",
        f"Exits(exit, exit) :- B{i}(exit).",
        f"Enters{i}(x, entry) :- Exits(x, exit), TC_boundary(exit, entry), B{i}(entry).",
        f"Path(x, y) :- Enters{i}(x, entry), T{i}(entry, y).",
        f"Path(x, entry) :- Enters{i}(x, entry).",
    )] + [(hub, rule) for rule in (
        "all_boundary(x, y) :- inter_boundary(x, y).",
        "TC_boundary(x, y) :- all_boundary(x, y).",
        "TC_boundary(x, y) :- TC_boundary(x, z), all_boundary(z, y).",
    )]


SHARDERS = {"metis": metis, "mod": mod}


def input_relations(shard_amt):
    return [f"E{i}" for i in range(shard_amt)] + [f"B{i}" for i in range(shard_amt)] + ["inter_boundary"]


def output_relations(shard_amt):
    return ["Path"]


def inputs(dataset, shard_amt, sharder):
    shard = SHARDERS[sharder](dataset, shard_amt)
    edges = sorted(dataset["edge"])
    cut = [(u, v) for u, v in edges if shard[u] != shard[v]]
    return ([(f"E{shard[u]}", (u, v)) for u, v in edges if shard[u] == shard[v]]
            + [("inter_boundary", e) for e in cut]
            + [(f"B{shard[v]}", (v,)) for v in sorted({v for e in cut for v in e})])


def check_correctness(dataset, outputs):
    return set(map(tuple, outputs["Path"])) == closure(dataset)

"""
A dataset is {"node": the nodes, "R", "S", "T": pairs of nodes, "Hash": triples of nodes}, nodes being ints.
"""
from .graphs_common import mod


def relations(shard_amt):
    n = range(shard_amt)
    return ({f"{r}{i}{j}": 2 for i in n for j in n for r in "RST"} | {f"Triangle{i}{j}{k}": 3 for i in n for j in n for k in n}
            | {"Hash": 3, "Interesting": 3})


def rules(shard_amt):
    n = range(shard_amt)
    return [((i * shard_amt + j) * shard_amt + k, rule) for i in n for j in n for k in n for rule in (
        f"Triangle{i}{j}{k}(x, y, z) :- R{i}{j}(x, y), S{j}{k}(y, z), T{k}{i}(z, x).",
        f"Interesting(x, y, z) :- Triangle{i}{j}{k}(x, y, z), Hash(x, y, z).",
    )]


SHARDERS = {"mod": mod}


def input_relations(shard_amt):
    n = range(shard_amt)
    return [f"{r}{i}{j}" for r in "RST" for i in n for j in n] + ["Hash"]


def output_relations(shard_amt):
    return ["Interesting"]


def inputs(dataset, shard_amt, sharder):
    shard = SHARDERS[sharder](dataset, shard_amt)
    return ([(f"{r}{shard[u]}{shard[v]}", (u, v)) for r in "RST" for u, v in sorted(dataset[r])]
            + [("Hash", t) for t in sorted(dataset["Hash"])])


def check_correctness(dataset, outputs):
    R, S, T = (dataset[r] for r in "RST")
    want = {(x, y, z) for x, y, z in dataset["Hash"] if (x, y) in R and (y, z) in S and (z, x) in T}
    return set(map(tuple, outputs["Interesting"])) == want

"""
A dataset here is {"node": the nodes, "edge": the directed edges (u, v), "start": the node the search starts from}, nodes being ints.
"""
from ..graphs import metis, mod, reachable


def relations(shard_amt):
    """maps each relation name to its arity"""
    return {"Reached": 1} | {f"Reached{i}": 1 for i in range(shard_amt)} | {f"E{i}_{j}": 2 for i in range(shard_amt) for j in range(shard_amt)}


def rules(shard_amt):
    """The rules, with a suggested 'ideal layout' (in this case, on 'shard_amt' nodes)"""
    return ([(i, f"Reached{j}(y) :- Reached{i}(x), E{i}_{j}(x, y).") for i in range(shard_amt) for j in range(shard_amt)]
            + [(i, f"Reached(x) :- Reached{i}(x).") for i in range(shard_amt)])


SHARDERS = {"metis": metis, "mod": mod}


def input_relations(shard_amt):
    return [f"E{i}_{j}" for i in range(shard_amt) for j in range(shard_amt)] + [f"Reached{i}" for i in range(shard_amt)]


def output_relations(shard_amt):
    return ["Reached"]


def inputs(dataset, shard_amt, sharder):
    region = SHARDERS[sharder](dataset, shard_amt)
    start = dataset["start"]
    return ([(f"E{region[u]}_{region[v]}", (u, v)) for u, v in sorted(dataset["edge"])]
            + [(f"Reached{region[start]}", (start,))])


def check_correctness(dataset, outputs):
    return {x for (x,) in outputs["Reached"]} == reachable(dataset)

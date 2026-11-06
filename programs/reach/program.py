"""
Single-source reachability on one node. A dataset is a graph with a start (see graphs.py); shard_amt is ignored.
"""
from ..graphs import reachable, unsharded


def relations(shard_amt):
    return {"E": 2, "Reached": 1}


def rules(shard_amt):
    return [(0, "Reached(y) :- Reached(x), E(x, y).")]


SHARDERS = {"none": unsharded}


def input_relations(shard_amt):
    return ["E", "Reached"]


def output_relations(shard_amt):
    return ["Reached"]


def inputs(dataset, shard_amt, sharder):
    return [("E", (u, v)) for u, v in sorted(dataset["edge"])] + [("Reached", (dataset["start"],))]


def check_correctness(dataset, outputs):
    return {x for (x,) in outputs["Reached"]} == reachable(dataset)

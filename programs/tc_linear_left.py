"""
A dataset is a graph (see graphs_common.py); shard_amt is ignored.
"""
from .graphs_common import closure, unsharded


def relations(shard_amt):
    return {"T": 2, "E": 2}


def rules(shard_amt):
    return [(0, "T(x, y) :- T(x, z), E(z, y)."), (0, "T(x, y) :- E(x, y).")]


SHARDERS = {"none": unsharded}


def input_relations(shard_amt):
    return ["E"]


def output_relations(shard_amt):
    return ["T"]


def inputs(dataset, shard_amt, sharder):
    return [("E", (u, v)) for u, v in sorted(dataset["edge"])]


def check_correctness(dataset, outputs):
    return set(map(tuple, outputs["T"])) == closure(dataset)


def layout_reasonable(shard_amt, rule_sets):
    return True

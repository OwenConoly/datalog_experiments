"""
Transitive closure on one node by repeated squaring: T{k} holds the pairs joined by a walk of exactly 2^k edges and
Tle{k} those joined by one of 1 to 2^k edges, so Tle{shard_amt} is the closure when no shortest path is longer than
2^shard_amt edges. shard_amt is the number of squarings, not shards. A dataset is a graph (see graphs_common.py).
"""
from .graphs_common import closure, unsharded

def relations(shard_amt):
    return {f"T{k}": 2 for k in range(max(shard_amt, 1))} | {f"Tle{k}": 2 for k in range(shard_amt + 1)} | {"E": 2}


"""
afrati and ullman, "transitive closure and recursive datalog implemented on clusters" discusses conditions under which this beats (i.e., has fewer  derivations than) the linear algorithm.  the answer seems to be that if there is any sparsity at all in the graph, then linear is going to win, with significantly smaller asymptotic complexity.  however, the paper concludes that the algorithms are "incomparable", meaning that one can artificially construct input graphs where either wins.

in addition to these asymptotic concerns, this has the unfortunate property of having a big constant factor compared to linear tc---lots of relations, all big, compared to linear tc's one big relation.
"""
def rules(shard_amt):
    return ([(0, "T0(x, y) :- E(x, y).")]
            + [(0, f"T{k}(x, y) :- T{k-1}(x, z), T{k-1}(z, y).") for k in range(1, shard_amt)]
            + [(0, "Tle0(x, y) :- T0(x, y).")]
            + [(0, rule) for k in range(1, shard_amt + 1)
               for rule in (f"Tle{k}(x, y) :- Tle{k-1}(x, y).", f"Tle{k}(x, y) :- Tle{k-1}(x, z), T{k-1}(z, y).")])


SHARDERS = {"none": unsharded}


def input_relations(shard_amt):
    return ["E"]


def output_relations(shard_amt):
    return [f"Tle{shard_amt}"]


def inputs(dataset, shard_amt, sharder):
    return [("E", (u, v)) for u, v in sorted(dataset["edge"])]


def check_correctness(dataset, outputs):
    (rows,) = outputs.values()
    return set(map(tuple, rows)) == closure(dataset)


def layout_reasonable(shard_amt, rule_sets):
    return True

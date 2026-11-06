"""
A chain with shortcuts: one path through all `size` nodes, in an order `seed` shuffles, plus an edge i -> i + d along it
for each d in 2..4 with probability 1/2 (about 2.5 edges out of a node, shortest paths about size/3 edges), and the
search starting at its head.
"""
import random


def generate(size, seed):
    rng = random.Random(seed)
    order = list(range(size))
    rng.shuffle(order)
    edges = {(i, i + 1) for i in range(size - 1)}
    edges |= {(i, i + d) for i in range(size) for d in range(2, 5) if i + d < size and rng.random() < 0.5}
    return {"node": set(order), "edge": {(order[u], order[v]) for u, v in edges}, "start": order[0]}

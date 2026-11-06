"""
A chain: one path through all `size` nodes, in an order `seed` shuffles (so the path's order isn't the nodes' order),
and the search starting at its head. Its longest shortest path is size - 1 edges.
"""
import random


def generate(size, seed):
    rng = random.Random(seed)
    order = list(range(size))
    rng.shuffle(order)
    return {"node": set(order), "edge": {(order[i], order[i + 1]) for i in range(size - 1)}, "start": order[0]}

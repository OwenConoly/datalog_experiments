"""
Dense random graphs: `size` nodes, each directed edge (self loops too) present with probability 1/2, and the search
starting at node 0.
"""
import random


def generate(size, seed):
    rng = random.Random(seed)
    edge = {(u, v) for u in range(size) for v in range(size) if rng.random() < 0.5}
    return {"node": set(range(size)), "edge": edge, "start": 0}

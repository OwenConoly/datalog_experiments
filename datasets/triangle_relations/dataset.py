"""
Three dense random relations over `size` nodes, R, S and T, each pair present with probability 1/2, and Hash: `size`
random triples (fewer if two coincide).
"""
import random


def generate(size, seed):
    rng = random.Random(seed)
    R, S, T = ({(i, j) for i in range(size) for j in range(size) if rng.random() < 0.5} for _ in range(3))
    triple = lambda: (rng.randrange(size), rng.randrange(size), rng.randrange(size))
    return {"node": set(range(size)), "R": R, "S": S, "T": T, "Hash": {triple() for _ in range(size)}}

"""
Random geometric graphs (https://en.wikipedia.org/wiki/Random_geometric_graph): `size` random points of a 65536 x 65536
grid, each joined both ways to every point within the distance that makes the average degree about 10, and the search
starting at the point nearest the middle. A point (x, y) is node x * 65536 + y, so a node fits in 32 bits.
"""
import math
import random

GRID = 65_536
DEGREE = 10


def generate(size, seed):
    rng = random.Random(seed)
    points = set()
    while len(points) < size:
        points.add((rng.randrange(GRID), rng.randrange(GRID)))
    radius = GRID * math.sqrt(DEGREE / (math.pi * size))
    cell = int(radius) + 1
    cells = {}
    for p in points:
        cells.setdefault((p[0] // cell, p[1] // cell), []).append(p)
    node = lambda p: p[0] * GRID + p[1]
    edge = {(node(p), node(q))
            for p in points
            for dx in (-1, 0, 1) for dy in (-1, 0, 1)
            for q in cells.get((p[0] // cell + dx, p[1] // cell + dy), ())
            if p != q and math.dist(p, q) <= radius}
    start = min(points, key=lambda p: (math.dist(p, (GRID / 2, GRID / 2)), p))
    return {"node": {node(p) for p in points}, "edge": edge, "start": node(start)}

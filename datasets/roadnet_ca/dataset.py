"""
Pieces of the California road network from SNAP (roadNet-CA, https://snap.stanford.edu/data/roadNet-CA.html): the
`size` nodes nearest, along roads, a node chosen by `seed` (breadth first: nearer nodes first, then smaller ids); every
road with both ends among them, in both directions; and the search starting at the chosen node. The data has no
coordinates, so a piece is cut by distance along roads rather than by a window, as Oldenburg's are.
roadNet-CA.txt.gz is downloaded from SNAP into this directory the first time it's needed.
"""
import functools
import gzip
import os
import random

from ..download_common import fetch

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "https://snap.stanford.edu/data/roadNet-CA.txt.gz"
FILE = os.path.join(HERE, "roadNet-CA.txt.gz")


@functools.cache
def roads():
    """Each node's neighbours, sorted, and the nodes, sorted."""
    adj = {}
    with gzip.open(fetch(URL, FILE), "rt") as f:
        for line in f:
            if not line.startswith("#"):
                u, v = map(int, line.split())
                if u != v:
                    adj.setdefault(u, set()).add(v)
                    adj.setdefault(v, set()).add(u)
    return {v: sorted(ns) for v, ns in adj.items()}, sorted(adj)


def generate(size, seed):
    adj, nodes = roads()
    start = random.Random(seed).choice(nodes)
    order, seen, frontier = [start], {start}, [start]
    while frontier and len(order) < size:
        frontier = sorted({v for u in frontier for v in adj[u]} - seen)
        seen.update(frontier)
        order += frontier
    node = set(order[:size])
    return {"node": node, "edge": {(u, v) for u in node for v in adj[u] if v in node}, "start": start}

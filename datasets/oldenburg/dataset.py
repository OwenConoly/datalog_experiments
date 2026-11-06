"""
Pieces of the Oldenburg road network (OL.cnode and OL.cedge: Feifei Li's spatial datasets,
https://users.cs.utah.edu/~lifeifei/SpatialDataset.htm): the `size` nodes nearest a node chosen by `seed`, distance being
max(|dx|, |dy|), so a square window; every road with both ends among them, in both directions; and the search starting
at the chosen node.
"""
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))


def generate(size, seed):
    pos = {}
    for line in open(os.path.join(HERE, "OL.cnode")):
        i, x, y = line.split()
        pos[int(i)] = (float(x), float(y))
    adj = {v: set() for v in pos}
    for line in open(os.path.join(HERE, "OL.cedge")):
        _, u, v, _ = line.split()
        u, v = int(u), int(v)
        if u != v:
            adj[u].add(v)
            adj[v].add(u)
    start = random.Random(seed).choice(sorted(pos))
    cx, cy = pos[start]
    node = set(sorted(pos, key=lambda v: (max(abs(pos[v][0] - cx), abs(pos[v][1] - cy)), v))[:size])
    edge = {(u, v) for u in node for v in adj[u] if v in node}
    return {"node": node, "edge": edge, "start": start}

"""
What the graph programs share: sharders over a dataset's nodes, and the answers they're checked against. A graph
dataset is {"node": the nodes, "edge": the directed edges (u, v)}, nodes being ints, with "start" for a single-source
search.
"""


def metis(dataset, shard_amt):
    import pymetis

    order = sorted(dataset["node"])
    local = {v: k for k, v in enumerate(order)}
    adj = {v: set() for v in order}
    for u, v in dataset["edge"]:
        if u != v:
            adj[u].add(v)
            adj[v].add(u)
    _, parts = pymetis.part_graph(shard_amt, adjacency=[[local[w] for w in sorted(adj[v])] for v in order])
    return dict(zip(order, parts))


def mod(dataset, shard_amt):
    return {v: v % shard_amt for v in dataset["node"]}


def unsharded(dataset, shard_amt):
    return {v: 0 for v in dataset["node"]}


def successors(dataset):
    succ = {}
    for u, v in dataset["edge"]:
        succ.setdefault(u, []).append(v)
    return succ


def reached_from(succ, sources):
    """Every node a path of one or more edges reaches from the sources, plus the sources."""
    reached, todo = set(sources), list(sources)
    while todo:
        for v in succ.get(todo.pop(), ()):
            if v not in reached:
                reached.add(v)
                todo.append(v)
    return reached


def reachable(dataset):
    """The nodes the start reaches, the start included."""
    return reached_from(successors(dataset), [dataset["start"]])


def closure(dataset):
    """The transitive closure: every (x, y) with a path of one or more edges from x to y."""
    succ = successors(dataset)
    return {(x, y) for x in succ for y in reached_from(succ, succ[x])}

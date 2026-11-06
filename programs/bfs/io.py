"""
A dataset here is {"node": the nodes, "edge": the directed edges (u, v), "start": the node the search starts from}, nodes being ints.
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


SHARDERS = {"metis": metis, "mod": mod}


def input_relations(shard_amt):
    return [f"E{i}_{j}" for i in range(shard_amt) for j in range(shard_amt)] + [f"Reached{i}" for i in range(shard_amt)]


def output_relations(shard_amt):
    return ["Reached"]


def inputs(dataset, shard_amt, sharder):
    region = SHARDERS[sharder](dataset, shard_amt)
    start = dataset["start"]
    return ([(f"E{region[u]}_{region[v]}", (u, v)) for u, v in sorted(dataset["edge"])]
            + [(f"Reached{region[start]}", (start,))])


def check_correctness(dataset, outputs):
    succ = {}
    for u, v in dataset["edge"]:
        succ.setdefault(u, []).append(v)
    reached, todo = {dataset["start"]}, [dataset["start"]]
    while todo:
        for v in succ.get(todo.pop(), ()):
            if v not in reached:
                reached.add(v)
                todo.append(v)
    return {x for (x,) in outputs["Reached"]} == reached

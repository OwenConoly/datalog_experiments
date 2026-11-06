def relations(shard_amt):
    """maps each relation name to its arity"""
    return {"Reached": 1} | {f"Reached{i}": 1 for i in range(shard_amt)} | {f"E{i}_{j}": 2 for i in range(shard_amt) for j in range(shard_amt)}


def rules(shard_amt):
    """The rules, with a suggested 'ideal layout' (in this case, on 'shard_amt' nodes)"""
    return ([(i, f"Reached{j}(y) :- Reached{i}(x), E{i}_{j}(x, y).") for i in range(shard_amt) for j in range(shard_amt)]
            + [(i, f"Reached(x) :- Reached{i}(x).") for i in range(shard_amt)])

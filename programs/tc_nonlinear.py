from .tc_linear_left import SHARDERS, check_correctness, input_relations, inputs, output_relations, relations


def rules(shard_amt):
    return [(0, "T(x, y) :- T(x, z), T(z, y)."), (0, "T(x, y) :- E(x, y).")]

from .tc_linear_left import SHARDERS, check_correctness, input_relations, inputs, layout_reasonable, output_relations, relations


def rules(shard_amt):
    return [(0, "T(x, y) :- E(z, y), T(x, z)."), (0, "T(x, y) :- E(x, y).")]

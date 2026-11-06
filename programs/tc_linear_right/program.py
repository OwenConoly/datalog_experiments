"""
Transitive closure on one node, linear, with the recursive clause second: tc_linear_left but for its rules.
"""
from ..tc_linear_left.program import SHARDERS, check_correctness, input_relations, inputs, output_relations, relations


def rules(shard_amt):
    return [(0, "T(x, y) :- E(z, y), T(x, z)."), (0, "T(x, y) :- E(x, y).")]

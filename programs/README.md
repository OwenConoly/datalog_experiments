# programs

Each program is `programs/<name>/program.py`, registered in `programs/__init__.py`:

```python
from .<name> import program as <name>

PROGRAMS = {..., "<name>": <name>}
```

A program is a family of Datalog programs over one parameter, `shard_amt`, whose meaning is the program's own (for
`bfs`, the number of shards its graph is split into). `program.py` must define:

| name | returns |
|---|---|
| `relations(shard_amt)` | `{relation: arity}` for every relation |
| `rules(shard_amt)` | the rules in order, as `(node, rule)` pairs: `rule` a Datalog rule ending in `.`, `node` its node in the program's suggested layout |
| `SHARDERS` | `{name: sharder}`: each `sharder(dataset, shard_amt)` assigns the dataset's items to shards `0 … shard_amt − 1` |
| `input_relations(shard_amt)` | the relations input facts enter, including any that may get none |
| `output_relations(shard_amt)` | the relations whose facts are the answer |
| `inputs(dataset, shard_amt, sharder)` | the input facts, as `(relation, args)` pairs with integer args |
| `check_correctness(dataset, outputs)` | whether `outputs` (`{relation: [args, …]}` for the output relations) is the right answer for `dataset` |

The suggested layout's nodes are numbered in the grid's (x, y) order, x varying slowest: `run.py`'s `ideal` placement
puts each rule on its node, while `single` and `compiler` ignore them. What a program needs from a dataset (for
`bfs`: `node`, `edge` and `start`) is said in its `program.py`'s docstring.

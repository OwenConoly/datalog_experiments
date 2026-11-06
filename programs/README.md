# programs

Each program is `programs/<name>.py`.
A dictionary mapping program names to modules (e.g.,"bfs" -> bfs.py) is maintained in `programs/__init__.py`.

A program is a family of Datalog programs over one parameter, `shard_amt`.

`<name>.py` must define:

| name | returns |
|---|---|
| `relations(shard_amt)` | `{relation: arity}` for every relation |
| `rules(shard_amt)` | the rules in order, as `(node, rule)` pairs: `rule` a Datalog rule ending in `.`, `node` its node in the program's suggested layout |
| `SHARDERS` | `{name: sharder}`: each `sharder(dataset, shard_amt)` assigns the dataset's items to shards `0 … shard_amt − 1` |
| `input_relations(shard_amt)` | the relations input facts enter, including any that may get none |
| `output_relations(shard_amt)` | the relations whose facts are the answer |
| `inputs(dataset, shard_amt, sharder)` | the input facts, as `(relation, args)` pairs with integer args |
| `check_correctness(dataset, outputs)` | whether `outputs` (`{relation: [args, …]}` for the output relations) is the right answer for `dataset` |

The format of `dataset` may be different for each program.

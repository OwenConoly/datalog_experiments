## Contents

- Example Datalog programs (`programs/`)
- Sanity checks for the layouts chosen by the distributing compiler (`tests/`)
- Experiments, using Benson's simulator to get performance numbers comparing some different programs (`comparisons/`)

## Setup

```sh
python -m venv .venv && .venv/bin/pip install pymetis matplotlib
export DATALOG_COMPILER=/path/to/distributing-datalog-compiler
export DATALOG_SIMULATOR=/path/to/distributed-datalog-simulator
```

## Running Tests

For example:

```sh
.venv/bin/python test_layout.py tests/bfs.json
```

Or, to run all the tests:

```sh
.venv/bin/python test_layout.py tests/*.json
```

## Comparisons

For example:

```sh
.venv/bin/python compare.py comparisons/bfs_roads.json
```

Or, to do all of them:

```sh
.venv/bin/python compare.py comparisons/*.json
```

Results (including the distributing compiler's output, and including a pretty performance plot) will be printed in `out/`.

To skip calling the simulator, and just get the compiled output corresponding to the comparisons, use the `--no-simulate` flag:

```sh
.venv/bin/python compare.py comparisons/bfs_roads.json --no-simulate
```

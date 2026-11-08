"""
Runs comparisons: each comparisons/NAME.json names its variants, each a program with the SHARD_AMT, SHARDER, PLACEMENT
and GRID run.py takes, and the datasets (each with its sizes) and seeds to run every variant on. Every run is
compiled, simulated and checked by run.py, in parallel, and comparisons given together share one pool. Everything about a
comparison goes in out/comparisons/NAME/: its compiled programs in compiled/, its runs' files in runs/, results.csv with
one row per run, and for each dataset DATASET.png, evaluation cycles (boot excluded, the mean over the seeds) against
size, one line per variant. A variant that doesn't compile is left out, and a wrong run isn't plotted.

    python compare.py [--no-simulate] comparisons/NAME.json [comparisons/OTHER.json ...]
    e.g. python compare.py comparisons/*.json

With --no-simulate it only compiles each comparison's programs, into out/comparisons/NAME/compiled/.
"""
import argparse
import csv
import json
import os
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter

import run
from compile import PLACEMENTS, checkout
from datasets import DATASETS
from programs import PROGRAMS

VARIANT = ("program", "shard_amt", "sharder", "placement", "grid")
COLUMNS = ("variant", "dataset", "size", "seed", "evaluation", "boot", "rounds", "correct", "error")
# the dataviz skill's categorical slots, in order: a variant's colour is its place in the file
COLORS = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948")
SURFACE, INK, MUTED, GRID_INK, AXIS_INK = "#fcfcfb", "#0b0b0b", "#898781", "#e1e0d9", "#c3c2b7"


def load(path):
    """The comparison, refused if it names something that doesn't exist."""
    c = json.load(open(path))
    problems = [f"no dataset {d!r}" for d in c["datasets"] if d not in DATASETS]
    for name, v in c["variants"].items():
        if sorted(v) != sorted(VARIANT):
            problems.append(f"{name!r} must give exactly {', '.join(VARIANT)}")
        elif v["program"] not in PROGRAMS:
            problems.append(f"{name!r}: no program {v['program']!r}")
        elif v["sharder"] not in PROGRAMS[v["program"]].SHARDERS:
            problems.append(f"{name!r}: {v['program']} has no sharder {v['sharder']!r}")
        elif v["placement"] not in PLACEMENTS:
            problems.append(f"{name!r}: no placement {v['placement']!r}")
    if len(c["variants"]) > len(COLORS):
        problems.append(f"at most {len(COLORS)} variants")
    if problems:
        sys.exit(f"{path}: " + "; ".join(problems))
    return c


def one(args):
    """One run, given as run.run's arguments in order; its result, or {"error": ...}."""
    try:
        return run.run(*args)
    except Exception as e:
        return {"error": str(e).strip().splitlines()[-1] if str(e).strip() else type(e).__name__}


def cycles(v):
    return f"{v / 1e6:g}M" if v >= 1e6 else f"{v / 1e3:g}k" if v >= 1e3 else f"{v:g}"


def plot(question, dataset, variants, rows, path):
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ends = []
    for name, color in zip(variants, COLORS):
        by_size = {}
        for r in rows:
            if r["variant"] == name and r.get("correct"):
                by_size.setdefault(r["size"], []).append(r["evaluation"])
        points = sorted((size, statistics.mean(e)) for size, e in by_size.items())
        if points:
            ax.plot(*zip(*points), color=color, linewidth=2, solid_capstyle="round", solid_joinstyle="round",
                    marker="o", markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.5, label=name)
            ends.append((name, points[-1]))
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.xaxis.set_major_locator(FixedLocator(sorted({r["size"] for r in rows})))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v / 1000:.2g}k" if v >= 1000 else f"{v:g}"))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: cycles(v)))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.grid(axis="y", which="major", color=GRID_INK, linewidth=1)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS_INK)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.set_xlabel(f"{dataset} size (log scale)", color=MUTED, fontsize=10)
    ax.set_ylabel("evaluation cycles, boot excluded (log scale)", color=MUTED, fontsize=10)
    ax.set_title(f"{question}\n{dataset}, simulated at L2", color=INK, fontsize=11, loc="left")
    ax.legend(frameon=False, labelcolor=INK, fontsize=9, loc="upper left", handlelength=4)
    if len(ends) <= 4:
        # direct labels at the lines' right ends, pushed apart where they'd overlap
        fig.subplots_adjust(right=0.75)
        fig.canvas.draw()
        gap, last = 12 * fig.dpi / 72, None
        for name, end in sorted(ends, key=lambda e: e[1][1]):
            y = ax.transData.transform(end)[1]
            moved = y if last is None else max(y, last + gap)
            ax.annotate(name, xy=end, xytext=(10, (moved - y) * 72 / fig.dpi), textcoords="offset points", va="center",
                        color=INK, fontsize=9, annotation_clip=False)
            last = moved
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comparisons", nargs="+", help="comparison files, e.g. comparisons/*.json")
    ap.add_argument("--no-simulate", action="store_true", help="only compile each comparison's programs")
    args = ap.parse_args()
    paths = args.comparisons
    comparisons = {path: load(path) for path in paths}
    outs = {path: os.path.join(run.OUT, "comparisons", os.path.splitext(os.path.basename(path))[0]) for path in paths}
    if len(set(outs.values())) < len(outs):
        sys.exit("two of the comparisons have the same name, so they'd share out/comparisons/NAME/")
    checkout("DATALOG_COMPILER", "distributing-datalog-compiler")
    if not args.no_simulate:
        checkout("DATALOG_SIMULATOR", "distributed-datalog-simulator")

    # each comparison's programs, compiled one at a time before any run, so parallel runs never compile the same
    # program at once
    variants = {}
    for path, c in comparisons.items():
        variants[path] = {}
        for name, v in c["variants"].items():
            try:
                run.compiled(v["program"], v["shard_amt"], v["placement"], v["grid"], outs[path])
                variants[path][name] = v
            except RuntimeError as e:
                print(f"{path}: {name}: left out, it didn't compile: {str(e).strip().splitlines()[-1]}", flush=True)
    if args.no_simulate:
        for path in paths:
            print(f"{path}: compiled programs in {os.path.relpath(os.path.join(outs[path], 'compiled'))}")
        return

    # every run, as run.run's arguments, roughly the biggest first, so the slowest runs start early
    jobs = [(path, name, (v["program"], v["shard_amt"], v["sharder"], v["placement"], v["grid"], dataset, size, seed, outs[path]))
            for path, c in comparisons.items() for dataset, sizes in c["datasets"].items() for size in sizes
            for seed in c["seeds"] for name, v in variants[path].items()]
    jobs.sort(key=lambda job: -job[2][6])
    with ProcessPoolExecutor() as pool:
        results = list(pool.map(one, [args for _, _, args in jobs]))

    for path, c in comparisons.items():
        out = outs[path]
        os.makedirs(out, exist_ok=True)
        order = list(variants[path])
        rows = [{"variant": name, "dataset": args[5], "size": args[6], "seed": args[7], **result}
                for (asker, name, args), result in zip(jobs, results) if asker == path]
        rows.sort(key=lambda r: (list(c["datasets"]).index(r["dataset"]), r["size"], r["seed"], order.index(r["variant"])))

        with open(os.path.join(out, "results.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, COLUMNS)
            w.writeheader()
            w.writerows(rows)
        width = max(map(len, order), default=7)
        print(f"\n== {path}")
        print(f"{'dataset':>18} {'size':>6} {'seed':>4} {'variant':>{width}} {'eval cycles':>12} {'rounds':>6} ok")
        for r in rows:
            head = f"{r['dataset']:>18} {r['size']:>6} {r['seed']:>4} {r['variant']:>{width}}"
            print(f"{head} ERROR {r['error']}" if "error" in r else
                  f"{head} {r['evaluation']:>12,} {r['rounds']:>6} {'yes' if r['correct'] else 'NO'}")
        for dataset in c["datasets"]:
            plot(c["question"], dataset, order, [r for r in rows if r["dataset"] == dataset], os.path.join(out, f"{dataset}.png"))
        print(f"results in {os.path.relpath(out)}")


if __name__ == "__main__":
    main()

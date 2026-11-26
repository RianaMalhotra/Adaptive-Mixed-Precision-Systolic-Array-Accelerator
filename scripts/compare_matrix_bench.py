import csv
import sys


def read(path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    return {(r["precision"], r["m"], r["k"], r["p"]): r for r in rows}


baseline, prefetch = map(read, sys.argv[1:3])
assert baseline and baseline.keys() == prefetch.keys()
print("precision,shape,baseline_cycles,prefetch_cycles,speedup,cycle_reduction_pct")
for key, b in baseline.items():
    p = prefetch[key]
    assert b["useful_macs"] == p["useful_macs"]
    old, new = int(b["cycles"]), int(p["cycles"])
    assert old > 0 and new > 0
    print(f"{key[0]},{'x'.join(key[1:])},{old},{new},{old/new:.3f},{100*(old-new)/old:.2f}")

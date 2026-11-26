#!/usr/bin/env python3
"""Map compute arrays to iCE40 logic and route an out-of-context design."""
import csv
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "synth" / "results"
OUT.mkdir(parents=True, exist_ok=True)
rows = []
for n in (2, 4, 8):
    stem = OUT / f"array_{n}"
    # Keep simulation assertion in original RTL; remove only this parameter guard
    # from the synthesis copy (ACC_W is fixed at 32).
    pe = (ROOT / "rtl/compute/mixed_precision_pe.sv").read_text()
    pe = re.sub(r"initial assert \(ACC_W >= 16\) else \$fatal\([^;]+;", "", pe)
    source = OUT / "mixed_precision_pe.sv"
    source.write_text(pe)
    script = (
        f"read_verilog -sv {source} {ROOT/'rtl/compute/systolic_array.sv'}; "
        f"hierarchy -top systolic_array -chparam N {n}; "
        f"synth_ice40 -top systolic_array -json {stem}.json"
    )
    with open(f"{stem}.yosys.log", "w") as log:
        subprocess.run(["yosys", "-p", script], stdout=log, stderr=subprocess.STDOUT, check=True)
    cells = json.loads(pathlib.Path(f"{stem}.json").read_text())["modules"]["systolic_array"]["cells"]
    types = [c["type"] for c in cells.values()]
    # The full accumulator bus is intentionally exposed; out-of-context routing
    # avoids treating thousands of internal result bits as physical package pins.
    row = dict(n=n, pes=n*n, lut4=types.count("SB_LUT4"),
               flip_flops=sum(t.startswith("SB_DFF") for t in types),
               carry=types.count("SB_CARRY"))
    report = pathlib.Path(f"{stem}.timing.json")
    with open(f"{stem}.nextpnr.log", "w") as log:
        proc = subprocess.run(["nextpnr-ice40","--hx8k","--package","ct256",
                               "--json",f"{stem}.json","--out-of-context",
                               "--freq","25","--timing-allow-fail",
                               "--report",str(report)],
                              stdout=log,stderr=subprocess.STDOUT)
    row["route_status"] = "ok" if proc.returncode == 0 else "failed"
    row["fmax_mhz"] = ""
    if proc.returncode == 0 and report.exists():
        clocks = json.loads(report.read_text()).get("fmax",{})
        achieved = [v["achieved"] for v in clocks.values() if "achieved" in v]
        if achieved:
            row["fmax_mhz"] = min(achieved)
    rows.append(row)
with (OUT/"summary.csv").open("w",newline="") as f:
    writer = csv.DictWriter(f,fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print((OUT/"summary.csv").read_text())

# TensorForge performance measurement

Run `make -C sim benchmark` to execute a cocotb regression that checks
hardware performance counters against measured clock cycles for 20
combinations: INT8 / packed INT4, K=1/4/8/16/32, and no stalls /
periodic backpressure (every fifth cycle).

Optionally write a machine-readable CSV:

```sh
TENSORFORGE_BENCH_CSV=benchmark.csv make -C sim benchmark
```

For N=4, the expected enabled compute cycles are K+2N-1, including
systolic fill/drain. Total elapsed compute-phase cycles include
stalls. Work is N*N*K INT8 MACs or 2*N*N*K scalar INT4 MACs.
Effective array utilization is useful scalar MACs divided by
elapsed cycles times peak scalar MACs per cycle (N*N for INT8;
2*N*N for packed INT4). It is a **cycle-based model**, not measured
clock frequency, physical throughput, area, energy or power.

The benchmark does not include host operand loading in the
compute-phase elapsed-cycle metric. Memory loading is currently
serialized through the host interface; the standalone ping-pong
buffer has not yet been integrated into the tile engine.

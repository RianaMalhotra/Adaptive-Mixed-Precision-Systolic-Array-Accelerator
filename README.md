# TensorForge — Adaptive Mixed-Precision AI Accelerator

A simulation-based SystemVerilog accelerator SoC project with mixed-precision
systolic compute, memory-aware scheduling, and cocotb verification.

## Implemented
- Parameterized N×N output-stationary systolic array
- Signed INT8 and dual signed packed INT4 MACs per processing element
- Register-array operand memories and programmable K-length tile engine
- Controller-generated operand skewing, stall handling and sticky done
- Compute-cycle and stall counters
- Randomized cocotb PE/array tests plus memory-backed tile scoreboards
- Verilator regression CI

**In progress:** Multi-tile M/N/K scheduling, ping-pong buffering, register
bus, interrupts, fault injection, and performance benchmarking.

## Run (Linux / WSL)
Install Verilator, make, and Python 3.11+.

```bash
python -m pip install -r requirements.txt
make -C sim
make -C sim array
make -C sim tile
```

See [architecture](docs/architecture.md) for memory layout and controller contract.

# TensorForge — Adaptive Mixed-Precision AI Accelerator

A SystemVerilog and cocotb project developing a configurable, tiled AI accelerator SoC with fault-aware verification.

## Implemented foundation
- Parameterized output-stationary N×N systolic compute array.
- Signed INT8 MAC and **two signed INT4 MACs per cycle** using packed nibbles.
- Configurable accumulator width (minimum 16 bits), synchronous clear, global stall.
- Deterministic cocotb randomized PE tests and matrix-multiplication scoreboard.
- Verilator regression workflow on pushes and pull requests.

**Status:** Compute foundation committed; simulation results and CI are not yet confirmed. Memory tiling, double buffering, register interface, fault injection, and performance analysis are planned—not implemented.

## Run locally (Linux / WSL)
Install Python 3.11+, Verilator and make.

```bash
python -m pip install -r requirements.txt
make -C sim
make -C sim array
```

## Data layout
Inputs are packed as N lanes of 8 bits each, least-significant lane first.
In INT8 mode each lane is a signed 8-bit value. In INT4 mode, each 8-bit
lane contains **two signed 4-bit values** (low nibble and high nibble).
For a tile with reduction index t, supply A[row,t] to row lane `row`
at cycle `t+row`, and B[t,col] to column lane `col` at cycle `t+col`.
Zero-pad unused lanes and run `K+2N-2` cycles after clear.
Read row-major ACC_W-bit signed output accumulators.

See [architecture and roadmap](docs/architecture.md).

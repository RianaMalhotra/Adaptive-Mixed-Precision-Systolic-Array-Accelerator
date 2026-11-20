# TensorForge architecture and roadmap

## Compute contract (implemented)
Output-stationary N x N array, signed INT8 or packed dual-lane INT4.
Each PE maintains a wrapping ACC_W-bit accumulator. Packed INT4 multiplies
corresponding signed low/high nibbles and sums both products per cycle.
The array accepts externally skewed row/column wavefronts. Inactive lanes
must be driven with zero. Assert clear between tiles; hold enable low to stall
the entire wavefront. Precision must remain fixed during a tile.

## Planned SoC datapath (not yet implemented)
Host register bus -> command FSM -> tile scheduler -> ping-pong input SRAM
-> systolic array -> output SRAM -> host readback.

M3: add SRAM abstraction, tiling across M/N/K, address generators.
M4: ping-pong buffers, valid/ready backpressure, overlap counters.
M5: memory-mapped registers, interrupts, command completion.
M6: transient/stuck-at fault injection, checker and sticky error status.
M7: workload benchmarks, utilization/throughput charts, Yosys reports.

## Verification principles
Use deterministic seeds, independent integer golden models, corner cases,
reset/clear/stall testing and eventual coverage reporting. Performance claims
must use measured RTL cycles; synthesis proxies are not physical area or power.

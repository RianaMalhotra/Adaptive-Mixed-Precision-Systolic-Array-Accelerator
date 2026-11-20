# TensorForge architecture

## Implemented compute foundation
Parameterized N x N output-stationary array with signed INT8 and dual-lane
signed packed INT4 arithmetic. Accumulation wraps at ACC_W bits.

## M3 phase 1: memory-backed reduction tiles
`tile_engine` stores A and B operands in behavioral register-array memories.
Host writes A[row*K_MAX + k] and B[k*N + col] while idle, sets reduction
length k_len and precision, and pulses start. The controller generates the
skewed wavefront, including zero padding, and holds the whole array on stalls.
Results are row-major signed ACC_W-bit values. done stays high until next
start; cycle_count tracks enabled compute cycles and stall_count disabled
busy cycles. k_len=0 is ignored.

The tile engine computes one N x N output tile, supporting variable K up to
K_MAX. The memories are register-array models, not physical SRAM macros.

## Remaining milestones
- M3 phase 2: multi-tile M/N/K scheduler and accumulation across K tiles
- M4: ping-pong SRAM and valid/ready backpressure
- M5: host register interface and interrupts
- M6: fault injection, detection and sticky fault status
- M7: performance benchmark plots and synthesis proxies

Simulation and CI verify functional behavior; area/power/timing are not yet measured.

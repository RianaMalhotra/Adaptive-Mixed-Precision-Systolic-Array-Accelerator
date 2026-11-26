# TensorForge architecture

## Compute and arithmetic

The parameterized N×N output-stationary array propagates signed operand bytes horizontally and vertically. INT8 computes one signed byte product per PE per enabled cycle. Packed INT4 computes the sum of two signed nibble products. Accumulation wraps at ACC_W bits (default 32). The tile engine generates the skewed wavefront and freezes compute on disabled cycles.

## Matrix data layout

A is row-major M×K and B is row-major K×P, with K expressed in operand bytes in both modes. Output C is M×P. Packed INT4 therefore performs twice as many scalar products for identical byte-shaped matrices. Local A addresses are row*K_MAX+k; local B addresses are k*N+column. Boundary lanes are zero padded.

The tile iterator traverses output row tiles, column tiles and reduction blocks. The writeback sequencer serializes PE results into the output accumulator. The first reduction block replaces an output entry; later blocks accumulate into it.

## Top-level variants

| Top | Operand staging |
|---|---|
| tensorforge_matrix_job_top | Host-fed tiles |
| tensorforge_autoload_top | Autonomous combinational source reads |
| tensorforge_sync_autoload_top | Registered source reads |
| tensorforge_pipelined_autoload_top | Pipelined one-cycle source reads |
| tensorforge_prefetch_top | Fixed-latency staging overlapped with compute |
| tensorforge_handshake_top | Variable-latency staging overlapped with compute |

## Prefetch and bank ownership

The prefetch controller launches a staged tile only when the engine and loader are idle and the previous writeback has completed. Launch advances the iterator and swaps the active operand bank. The next tile is loaded into the inactive bank while the current tile computes. Launched row/column and first-block metadata are retained until writeback. Job completion follows the final writeback. overlap_cycles counts simultaneous loader and engine busy cycles.

## Variable-latency memory contract

For each A/B port, read acts as request valid, req_ready accepts the request, and read_addr identifies a byte. The source returns read_data with rsp_valid and retains both until rsp_ready. The loader supports one outstanding transaction across both ports and accepts responses after request acceptance. It holds request address and valid while blocked. Padding slots require no external request. Reset cancels local outstanding state; the external source must discard stale responses on reset. This is not AXI.

## Host registers and DFX

accelerator_regs wraps the tile engine with host controls and completion interrupt. result_fault_monitor injects XOR corruption into the observed result, compares it with the original result, and records sticky status, first failing index and counters. This is a diagnostic path rather than independent redundant computation. The matrix tops do not expose the full register/DFX wrapper.

## Verification and implementation studies

Cocotb tests cover arithmetic, scheduling, memory loading, writeback, randomized compute stalls, memory handshakes and result-path fault injection. The matched benchmark runs identical operands and shapes on baseline and prefetch tops. The synthesis script maps the compute array to iCE40 HX8K logic and attempts out-of-context routing at 25 MHz for N=2,4,8. Routing failures are recorded rather than treated as timing measurements.

All memories are behavioral models. Full accelerator physical timing, power, board validation and independent compute fault coverage remain outside the current scope. Check CI artifacts for actual results.

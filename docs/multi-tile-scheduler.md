# Integrated multi-tile sequencing

The tensorforge_multitile_top module connects multi_tile_scheduler to
double_buffered_tile_engine. Host configures requested_tiles, stages one
tile into the inactive operand bank, and asserts tile_ready. The scheduler
starts the engine and waits for completion before issuing subsequent starts.

The integrated cocotb regression executes three tiles with varying K and
INT8/packed INT4, checking the full output accumulator matrix each time.

This is host-assisted sequencing, not a fully autonomous matrix GEMM:
there is no DMA, output-tile writeback, automatic matrix address
generation, or guarantee of simultaneous host load and compute in the
integrated regression. Those are future milestones.

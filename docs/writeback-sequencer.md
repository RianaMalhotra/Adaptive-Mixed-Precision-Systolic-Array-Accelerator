# Automatic tile-result serialization

tile_writeback_sequencer detects a rising edge of engine_done, snapshots
all N*N accumulator words and the host-provided output tile coordinates,
then emits one write per clock cycle in row-major order. The transfer
takes N*N cycles after capture and ends with a one-cycle transfer_done
pulse. A result-bus change during transfer does not corrupt the snapshot.

The write interface maps directly to output_accumulator's write_valid,
tile_row/tile_col, row_lane/col_lane, first_k_block, and partial_sum.

This milestone verifies the sequencer independently. It does not yet
connect it to the output accumulator or prevent an upstream scheduler
from launching the next compute tile during writeback. Integration and
backpressure are the next milestone.

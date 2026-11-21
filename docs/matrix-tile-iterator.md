# Automatic matrix tile traversal

The matrix_tile_iterator enumerates output tiles in row-major order
and reduction chunks within each output tile. A start command latches
the matrix dimensions and begins at tile (0,0), reduction block 0.
Each tile_advance pulse moves to the next reduction block or output
tile. The current_k_len output shortens the final reduction chunk,
and first_k_block marks the writeback overwrite operation.

The iterator supports zero dimensions by completing immediately.
It is a standalone control block; it does not yet issue operand
memory reads, drive the compute engine, or schedule writeback.
Those connections are the next integration milestone.

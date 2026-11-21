# Matrix address generation

The standalone matrix_tile_address_gen computes row-major byte offsets
for operand A (M x K), operand B (K x P), and output C (M x P).
Inputs identify the output tile row/column, reduction block, and local
row/column/reduction lanes. A/B/C validity outputs mask boundaries.

For array size N and reduction chunk K_TILE:
- A row = tile_row*N + row_lane
- B column = tile_col*N + col_lane
- reduction coordinate = k_block*K_TILE + reduction_lane
- A offset = row*K + reduction coordinate
- B offset = reduction coordinate*P + column
- C offset = row*P + column

Offsets are byte indices for INT8 or packed INT4 operand bytes; C offset
is a logical accumulator-word index, not a byte offset. No physical
memory reads or result writes are performed by this module. It does not
yet handle reduction-block accumulation across separate engine runs.

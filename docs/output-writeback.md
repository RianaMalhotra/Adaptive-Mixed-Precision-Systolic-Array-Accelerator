# Output accumulation and writeback

The standalone output_accumulator stores a logical M x P output matrix
in on-chip register-array memory, parameterized by MAX_M/MAX_P.
A write supplies the output tile coordinate, local row/column lane,
and partial sum. The module computes the physical row/column, masks
out-of-bounds lanes, and either overwrites the C entry for the first
reduction block or adds to it for subsequent reduction blocks.

Accumulation is modulo 2**ACC_W, matching fixed-width hardware.
The read port provides logical row/column access and a valid flag.
An accepted_writes counter supports diagnostics.

The module is not yet wired to the engine result bus. A future
sequencer must emit the N*N writeback transactions per completed
tile and manage reduction-block order. This design does not implement
DRAM, DMA, AXI, or an external memory controller.

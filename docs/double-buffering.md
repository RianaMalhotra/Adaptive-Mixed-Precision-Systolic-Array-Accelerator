# Double-buffered tile engine

The double_buffered_tile_engine is an integrated two-bank version of the
compute tile engine. The host writes the inactive bank even when busy,
while the compute wavefront reads the active bank. On each accepted start,
bank ownership swaps, the array clears, and a new tile begins. A tile's
operands must be fully loaded into the inactive bank before start.

The interface uses the same row-major addressing as tile_engine.
The active_bank output exposes which bank compute is consuming.
The new cocotb test loads tile 1 while tile 0 is computing, then
checks INT8 and packed INT4 results across successive bank swaps.

This is not yet a multi-tile scheduler or an AXI-ready memory interface.
Host software must coordinate tile boundaries and prevent overwriting
the inactive bank before its next start.

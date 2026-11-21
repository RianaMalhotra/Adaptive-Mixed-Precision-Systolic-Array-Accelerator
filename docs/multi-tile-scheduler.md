# Multi-tile sequencing

The standalone multi_tile_scheduler issues one-cycle start pulses to a
tile engine when a host-provided tile_ready credit is present and the
engine is idle. The host configures a target tile count and stages
each tile into the engine's inactive bank before asserting tile_ready.
A single outstanding credit is supported.

The controller counts launches and rising-edge completions, handles
host preparation delays, and sets all_done after the final tile.
It does not implement automatic operand address generation, DMA,
result accumulation across output tiles, or output-memory writeback.

The scheduler is separately verified before integration with the
double_buffered_tile_engine. Do not interpret this milestone as a
fully autonomous matrix-multiplication controller.

# Integrated tile writeback

The multi-tile top snapshots completed engine results, serializes each output tile into the output accumulator, and blocks launches while writeback is busy. The all_done output waits for the last writeback to drain. The regression reads back the complete 4x4 output after each of three tiles.

The host must hold first_k_block stable through the engine completion edge. Tile coordinates are latched at launch. Operand staging and tile metadata remain host-controlled; DMA and autonomous traversal are not implemented.

# DFX integration

The memory-mapped accelerator integrates the standalone result fault monitor.
Select an accumulator with RESULT_INDEX (0x18), set XOR mask at 0x34,
and enable injection with bit 0 of DFX_CTRL (0x30).
RESULT_DATA (0x1c) returns the potentially injected result.

Writing DFX_CTRL bit 1 samples the selected result (only when idle).
Bit 2 clears diagnostics. DFX_STATUS (0x38) reports sticky fault
(bit 0) and current mismatch (bit 1). DFX_SAMPLES (0x3c),
DFX_FAULTS (0x40), and DFX_FIRST_INDEX (0x44) expose diagnostics.

This is test instrumentation comparing against the same original
accumulator, not independent fault-tolerant compute. Existing IRQ
indicates tile completion only.

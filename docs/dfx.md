# TensorForge DFX result monitor

The standalone `result_fault_monitor` compares an intentionally XOR-corrupted
observed accumulator word with the unmodified accumulator reference. On
`sample_valid`, a nonzero mismatch increments `fault_count`, asserts a sticky
fault flag and captures the first failing result index. `sample_count` tracks
all valid observations. Reset or `clear_status` resets diagnostics.

This is **fault injection test infrastructure**, not production fault-tolerant
hardware: both paths derive from the same original accumulator. It cannot
detect a common-mode computation error and does not provide ECC, TMR,
scan insertion or fault coverage claims. The next step is to connect the
monitor to the register interface and measure injected-fault detection.

# Matrix job performance benchmark

The autoload and sync_autoload cocotb regressions report BENCH lines for INT8 and packed INT4 on identical 5x33 by 33x5 byte-shaped operands. All output cells remain checked against Python references.

Metrics: rising edges after the accepted start edge until job_done, useful scalar MACs (825 INT8 or 1650 packed INT4), and useful MACs per cycle. Packed INT4 represents two scalar reduction lanes per byte, so this is equal byte traffic rather than equal scalar workload. Padding is excluded from useful work. The clock period is a simulation setting, not a measured hardware Fmax.

Run make -C sim autoload and make -C sim sync_autoload; inspect BENCH lines in the logs. Results are pending CI; no measured speedup is claimed yet.

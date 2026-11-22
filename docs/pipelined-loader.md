# Pipelined SRAM operand loader

A request is issued every cycle while the preceding response is written to the inactive bank. Registered metadata preserves the destination address, bank selector and padding flag. A drain cycle commits the last response before done. The standalone regression checks 256 writes in 257 cycles after start, including padding. The previous two-phase loader remains available. This assumes fixed one-cycle read latency without backpressure. Full matrix integration and measured speedup remain future work.

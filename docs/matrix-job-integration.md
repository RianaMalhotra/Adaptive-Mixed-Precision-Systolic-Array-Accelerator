# Host-fed full matrix execution

tensorforge_matrix_job_top wires the matrix iterator, job FSM,
double-buffered compute engine, tile-result serializer and C accumulator.
The controller supplies output tile coordinates, reduction block index
and K length. After each engine completion, the writeback serializer
drains all N*N outputs before the controller advances. The first
reduction block overwrites each output; later blocks accumulate.

The integration regression performs signed INT8 multiplication for
A[5,33] and B[33,5], including boundary tiles and a partial reduction
block, and checks the full C[5,5] matrix against a Python reference.

The host still stages A/B bytes into the inactive bank on every tile
and pulses operands_ready. This is not DMA or a fully autonomous
operand loader. Packed INT4 matrix-level integration is future work.

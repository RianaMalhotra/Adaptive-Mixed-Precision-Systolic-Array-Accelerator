# Matrix job orchestration

matrix_job_controller integrates matrix_tile_iterator with a handshake FSM:
PREPARE waits for operands_ready, LAUNCH pulses engine_start,
COMPUTE waits for a rising edge on engine_done, WRITEBACK waits for
writeback_done, and ADVANCE consumes the current tile coordinate.
This ensures the next tile is not dispatched until the previous
writeback finishes. The iterator provides tile coordinates, the
partial reduction length and first/last block flags.

The test covers an M=5, K=33, P=5 matrix (8 reduction/output tiles)
with deliberate stalls in both operand preparation and writeback.

The controller is independently verified. Connecting these handshakes
to actual operand memory and the existing integrated compute/writeback
top remains future work. The host still stages operand tiles.

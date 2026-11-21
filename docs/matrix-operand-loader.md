# Matrix operand loader

The matrix_operand_loader converts row-major A[M,K] and B[K,P]
addresses into the compute engine's local A and B bank addresses.
Each start request streams N*K_TILE bytes for A followed by
N*K_TILE bytes for B, with zero padding for matrix edges and
short reduction blocks. A and B source memory use combinational
read ports; data is expected to be valid during the same cycle
as the read address. A done pulse signals staging completion.

The loader is independently verified with a partial output tile
and one-element final reduction block. It has not yet been
connected to the matrix-job top. Synchronous SRAM will require
an address/data pipeline and explicit read latency handling.

// TensorForge matrix-tile address generator.
// Matrix A is M x K, B is K x P, both row-major byte arrays.
// A output tile is selected by tile_row, B by tile_col, reduction
// chunk by k_block. Returns byte offsets and lane-valid mask.
// Addresses are 32-bit byte offsets; host must ensure no overflow.
module matrix_tile_address_gen #(
    parameter int N = 4,
    parameter int K_TILE = 32,
    parameter int IDX_W = 16
) (
    input logic [IDX_W-1:0] m_dim, k_dim, p_dim,
    input logic [IDX_W-1:0] tile_row, tile_col, k_block,
    input logic [$clog2(N)-1:0] row_lane, col_lane,
    input logic [$clog2(K_TILE)-1:0] reduction_lane,
    output logic [31:0] a_offset, b_offset, c_offset,
    output logic a_valid, b_valid, c_valid
);
    logic [31:0] global_row, global_col, global_k;
    always_comb begin
        global_row = 32'(tile_row)*N + 32'(row_lane);
        global_col = 32'(tile_col)*N + 32'(col_lane);
        global_k = 32'(k_block)*K_TILE + 32'(reduction_lane);
        a_valid = (global_row < 32'(m_dim)) && (global_k < 32'(k_dim));
        b_valid = (global_k < 32'(k_dim)) && (global_col < 32'(p_dim));
        c_valid = (global_row < 32'(m_dim)) && (global_col < 32'(p_dim));
        a_offset = global_row*32'(k_dim) + global_k;
        b_offset = global_k*32'(p_dim) + global_col;
        c_offset = global_row*32'(p_dim) + global_col;
    end
endmodule

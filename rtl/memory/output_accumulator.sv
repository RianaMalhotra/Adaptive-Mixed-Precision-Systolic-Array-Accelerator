// TensorForge output accumulation/writeback for reduction-block tiles.
// One result word accepted per cycle. A tile's partial sum is accumulated
// into the logical C matrix at (tile_row*N+row_lane, tile_col*N+col_lane).
// first_k_block overwrites previous C for that coordinate; subsequent
// reduction blocks add modulo 2**ACC_W. Writes outside M/P are masked.
// Host reads are combinational. No concurrent read/write arbitration.
module output_accumulator #(
    parameter int N = 4,
    parameter int MAX_M = 32,
    parameter int MAX_P = 32,
    parameter int ACC_W = 32,
    parameter int IDX_W = 16
) (
    input logic clk, rst_n,
    input logic [IDX_W-1:0] m_dim, p_dim,
    input logic write_valid,
    input logic first_k_block,
    input logic [IDX_W-1:0] tile_row, tile_col,
    input logic [$clog2(N)-1:0] row_lane, col_lane,
    input logic [ACC_W-1:0] partial_sum,
    output logic write_accepted,
    input logic [IDX_W-1:0] read_row, read_col,
    output logic [ACC_W-1:0] read_data,
    output logic read_valid,
    output logic [31:0] accepted_writes
);
    logic [ACC_W-1:0] c_mem [0:MAX_M*MAX_P-1];
    logic [31:0] global_row, global_col;
    logic [31:0] write_index, read_index;
    always_comb begin
        global_row = 32'(tile_row)*N + 32'(row_lane);
        global_col = 32'(tile_col)*N + 32'(col_lane);
        write_index = global_row*MAX_P + global_col;
        read_index = 32'(read_row)*MAX_P + 32'(read_col);
        write_accepted = write_valid &&
            (global_row < 32'(m_dim)) && (global_col < 32'(p_dim)) &&
            (global_row < MAX_M) && (global_col < MAX_P);
        read_valid = (32'(read_row) < 32'(m_dim)) &&
            (32'(read_col) < 32'(p_dim)) &&
            (32'(read_row) < MAX_M) && (32'(read_col) < MAX_P);
        read_data = '0;
        if (read_valid)
            read_data = c_mem[read_index];
    end
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            accepted_writes <= '0;
        end else if (write_accepted) begin
            if (first_k_block)
                c_mem[write_index] <= partial_sum;
            else
                c_mem[write_index] <= c_mem[write_index] + partial_sum;
            accepted_writes <= accepted_writes + 1'b1;
        end
    end
endmodule

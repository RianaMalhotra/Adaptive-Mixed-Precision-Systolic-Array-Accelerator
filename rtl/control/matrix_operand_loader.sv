// Streams row-major matrix operands into the engine's inactive tile bank.
// External source memory is read through a combinational address/data port.
// One byte is written per clock; the host no longer computes tile addresses.
module matrix_operand_loader #(
    parameter int N = 4,
    parameter int K_TILE = 32,
    parameter int ADDR_W = $clog2(N*K_TILE),
    parameter int IDX_W = 16,
    parameter int MEM_ADDR_W = 32
) (
    input logic clk, rst_n, start,
    input logic [IDX_W-1:0] m_dim, k_dim, p_dim,
    input logic [IDX_W-1:0] tile_row, tile_col, k_block,
    input logic [$clog2(K_TILE+1)-1:0] current_k_len,
    output logic busy, done,
    output logic a_write, b_write,
    output logic [ADDR_W-1:0] write_addr,
    output logic [7:0] write_data,
    output logic a_read, b_read,
    output logic [MEM_ADDR_W-1:0] a_read_addr, b_read_addr,
    input logic [7:0] a_read_data, b_read_data
);
    logic [$clog2(2*N*K_TILE+1)-1:0] cursor;
    logic [$clog2(N+1)-1:0] lane;
    logic [$clog2(K_TILE+1)-1:0] k_lane;
    logic [IDX_W-1:0] global_row, global_col, global_k;
    logic in_a, valid_element;
    logic [ADDR_W-1:0] local_addr;
    always_comb begin
        in_a = (cursor < N*K_TILE);
        if (in_a) begin
            lane = ($clog2(N+1))'(cursor / K_TILE);
            k_lane = ($clog2(K_TILE+1))'(cursor % K_TILE);
        end else begin
            lane = ($clog2(N+1))'((cursor - (2*N*K_TILE)'(N*K_TILE)) % N);
            k_lane = ($clog2(K_TILE+1))'((cursor - (2*N*K_TILE)'(N*K_TILE)) / N);
        end
        global_row = IDX_W'(tile_row*N + lane);
        global_col = IDX_W'(tile_col*N + lane);
        global_k = IDX_W'(k_block*K_TILE + k_lane);
        valid_element = (k_lane < current_k_len) &&
            (in_a ? (global_row < m_dim) : (global_col < p_dim));
        local_addr = ADDR_W'(in_a ? (lane*K_TILE + k_lane) : (k_lane*N + lane));
        a_write = busy && in_a;
        b_write = busy && !in_a;
        write_addr = local_addr;
        a_read = a_write && valid_element;
        b_read = b_write && valid_element;
        a_read_addr = MEM_ADDR_W'(global_row)*MEM_ADDR_W'(k_dim) + MEM_ADDR_W'(global_k);
        b_read_addr = MEM_ADDR_W'(global_k)*MEM_ADDR_W'(p_dim) + MEM_ADDR_W'(global_col);
        write_data = valid_element ? (in_a ? a_read_data : b_read_data) : 8'h00;
    end
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            busy <= 1'b0;
            done <= 1'b0;
            cursor <= '0;
        end else begin
            done <= 1'b0;
            if (start && !busy) begin
                busy <= 1'b1;
                cursor <= '0;
            end else if (busy) begin
                if (cursor == (2*N*K_TILE)-1) begin
                    busy <= 1'b0;
                    done <= 1'b1;
                end else begin
                    cursor <= cursor + 1'b1;
                end
            end
        end
    end
endmodule

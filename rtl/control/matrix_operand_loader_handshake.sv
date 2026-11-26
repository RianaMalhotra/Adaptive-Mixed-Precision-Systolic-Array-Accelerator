// Variable-latency loader: one outstanding request, in-order response.
module matrix_operand_loader_handshake #(
    parameter int N=4, K_TILE=32,
    parameter int ADDR_W=$clog2(N*K_TILE),
    parameter int IDX_W=16,
    parameter int MEM_ADDR_W=32
) (
    input logic clk, rst_n, start,
    input logic [IDX_W-1:0] m_dim,k_dim,p_dim,
    input logic [IDX_W-1:0] tile_row,tile_col,k_block,
    input logic [$clog2(K_TILE+1)-1:0] current_k_len,
    output logic busy,done,
    output logic a_read,b_read,
    output logic [MEM_ADDR_W-1:0] a_read_addr,b_read_addr,
    input logic [7:0] a_read_data,b_read_data,
    input logic a_req_ready,b_req_ready,a_rsp_valid,b_rsp_valid,
    output logic a_rsp_ready,b_rsp_ready,
    output logic a_write,b_write,
    output logic [ADDR_W-1:0] write_addr,
    output logic [7:0] write_data
);
    typedef enum logic [1:0] {IDLE,REQUEST,RESPONSE} state_t;
    state_t state;
    logic [$clog2(2*N*K_TILE+1)-1:0] cursor;
    logic in_a, valid_element;
    logic [31:0] offset, lane, k_lane;
    logic [31:0] global_row,global_col,global_k;
    logic [ADDR_W-1:0] local_addr;
    logic complete_slot;
    always_comb begin
        in_a = 32'(cursor) < N*K_TILE;
        offset = in_a ? 32'(cursor) : 32'(cursor) - N*K_TILE;
        lane = in_a ? offset/K_TILE : offset%N;
        k_lane = in_a ? offset%K_TILE : offset/N;
        global_row = 32'(tile_row)*N+lane;
        global_col = 32'(tile_col)*N+lane;
        global_k = 32'(k_block)*K_TILE+k_lane;
        valid_element = k_lane < 32'(current_k_len) &&
                        (in_a ? global_row < 32'(m_dim) : global_col < 32'(p_dim));
        local_addr = ADDR_W'(in_a ? lane*K_TILE+k_lane : k_lane*N+lane);
        a_read = state == REQUEST && in_a && valid_element;
        b_read = state == REQUEST && !in_a && valid_element;
        a_read_addr = MEM_ADDR_W'(global_row)*MEM_ADDR_W'(k_dim)+MEM_ADDR_W'(global_k);
        b_read_addr = MEM_ADDR_W'(global_k)*MEM_ADDR_W'(p_dim)+MEM_ADDR_W'(global_col);
        a_rsp_ready = state == RESPONSE && in_a;
        b_rsp_ready = state == RESPONSE && !in_a;
        complete_slot = (state == REQUEST && !valid_element) ||
                        (state == RESPONSE && (in_a ? a_rsp_valid : b_rsp_valid));
        a_write = complete_slot && in_a;
        b_write = complete_slot && !in_a;
        write_addr = local_addr;
        write_data = valid_element ? (in_a ? a_read_data : b_read_data) : 8'h00;
        busy = state != IDLE;
    end
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state <= IDLE;
            cursor <= '0;
            done <= 1'b0;
        end else begin
            done <= 1'b0;
            if (state == IDLE) begin
                if (start) begin
                    cursor <= '0;
                    state <= REQUEST;
                end
            end else if (complete_slot) begin
                if (32'(cursor) == 2*N*K_TILE-1) begin
                    state <= IDLE;
                    done <= 1'b1;
                end else begin
                    cursor <= cursor + 1'b1;
                    state <= REQUEST;
                end
            end else if (state == REQUEST && valid_element &&
                         (in_a ? a_req_ready : b_req_ready)) begin
                state <= RESPONSE;
            end
        end
    end
endmodule

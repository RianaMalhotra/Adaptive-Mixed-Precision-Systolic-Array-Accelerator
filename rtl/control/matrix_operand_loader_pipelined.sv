// One-cycle synchronous SRAM operand loader.
// Request at cycle T, sample registered SRAM data and write tile at T+1.
// Assumes source read_data is stable during the WRITE phase.
module matrix_operand_loader_pipelined #(
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
    output logic a_write,b_write,
    output logic [ADDR_W-1:0] write_addr,
    output logic [7:0] write_data
);
    typedef enum logic [1:0] {IDLE,REQUEST,DRAIN} state_t;
    state_t state;
    logic [$clog2(2*N*K_TILE+1)-1:0] cursor;
    logic in_a, valid_element;
    logic [31:0] offset, lane, k_lane;
    logic [31:0] global_row,global_col,global_k;
    logic [ADDR_W-1:0] local_addr;
    logic held_a, held_valid, pending;
    logic [ADDR_W-1:0] held_addr;
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
        a_write = pending && held_a;
        b_write = pending && !held_a;
        write_addr = held_addr;
        write_data = held_valid ? (held_a ? a_read_data : b_read_data) : 8'h00;
        busy = state != IDLE;
    end
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state <= IDLE;
            cursor <= '0;
            held_a <= 1'b0;
            held_valid <= 1'b0;
            held_addr <= '0;
            pending <= 1'b0;
            done <= 1'b0;
        end else begin
            done <= 1'b0;
            case (state)
                IDLE: if (start) begin
                    pending <= 1'b0;
                    cursor <= '0;
                    state <= REQUEST;
                end
                REQUEST: begin
                    held_a <= in_a;
                    held_valid <= valid_element;
                    held_addr <= local_addr;
                    pending <= 1'b1;
                    if (32'(cursor) == 2*N*K_TILE-1)
                        state <= DRAIN;
                    else
                        cursor <= cursor + 1'b1;
                end
                DRAIN: begin
                    pending <= 1'b0;
                    state <= IDLE;
                    done <= 1'b1;
                end
                default: begin
                    pending <= 1'b0;
                    state <= IDLE;
                end
            endcase
        end
    end
endmodule

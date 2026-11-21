// Autonomous operand staging from combinational row-major matrix memory.
// Host supplies A/B source read data, not per-tile writes or ready pulses.
module tensorforge_autoload_top #(
    parameter int N = 4,
    parameter int K_MAX = 32,
    parameter int ACC_W = 32,
    parameter int ADDR_W = $clog2(N*K_MAX)
) (
    input logic clk, rst_n, start, enable, mode_int4,
    input logic [15:0] m_dim, k_dim, p_dim,
    output logic a_read, b_read,
    output logic [31:0] a_read_addr, b_read_addr,
    input logic [7:0] a_read_data, b_read_data,
    input logic [15:0] read_row, read_col,
    output logic [ACC_W-1:0] read_data,
    output logic read_valid, job_done,
    output logic loader_busy, engine_busy, writeback_busy,
    output logic [31:0] tiles_visited, accepted_writes
);
    logic waiting_for_operands, waiting_for_engine, waiting_for_writeback;
    logic active_bank, first_k_block, last_k_block;
    logic [15:0] tile_row, tile_col, k_block;
    logic [$clog2(K_MAX+1)-1:0] current_k_len;
    logic load_started, load_done, load_start;
    logic a_write, b_write;
    logic [ADDR_W-1:0] write_addr;
    logic [7:0] write_data;
    // Prevent repeated loader starts while PREPARE remains asserted.
    assign load_start = waiting_for_operands && !load_started && !loader_busy;
    always_ff @(posedge clk) begin
        if (!rst_n) load_started <= 1'b0;
        else if (!waiting_for_operands) load_started <= 1'b0;
        else if (load_start) load_started <= 1'b1;
    end
    matrix_operand_loader #(.N(N), .K_TILE(K_MAX), .ADDR_W(ADDR_W)) loader (
        .clk(clk), .rst_n(rst_n), .start(load_start),
        .m_dim(m_dim), .k_dim(k_dim), .p_dim(p_dim),
        .tile_row(tile_row), .tile_col(tile_col), .k_block(k_block),
        .current_k_len(current_k_len), .busy(loader_busy), .done(load_done),
        .a_write(a_write), .b_write(b_write), .write_addr(write_addr),
        .write_data(write_data), .a_read(a_read), .b_read(b_read),
        .a_read_addr(a_read_addr), .b_read_addr(b_read_addr),
        .a_read_data(a_read_data), .b_read_data(b_read_data)
    );
    tensorforge_matrix_job_top #(.N(N), .K_MAX(K_MAX), .ACC_W(ACC_W)) job (
        .clk(clk), .rst_n(rst_n), .start(start),
        .operands_ready(load_done), .enable(enable), .mode_int4(mode_int4),
        .m_dim(m_dim), .k_dim(k_dim), .p_dim(p_dim),
        .a_write(a_write), .b_write(b_write),
        .write_addr(write_addr), .write_data(write_data),
        .read_row(read_row), .read_col(read_col), .read_data(read_data),
        .read_valid(read_valid), .job_done(job_done),
        .waiting_for_operands(waiting_for_operands),
        .waiting_for_engine(waiting_for_engine),
        .waiting_for_writeback(waiting_for_writeback),
        .engine_busy(engine_busy), .writeback_busy(writeback_busy),
        .active_bank(active_bank), .tile_row(tile_row),
        .tile_col(tile_col), .k_block(k_block),
        .current_k_len(current_k_len), .first_k_block(first_k_block),
        .last_k_block(last_k_block), .tiles_visited(tiles_visited),
        .accepted_writes(accepted_writes)
    );
endmodule

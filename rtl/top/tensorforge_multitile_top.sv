// Host-assisted, double-buffered multi-tile top.
// Host must stage the next tile in the inactive bank and pulse tile_ready.
// Results are readable between tile completions; no output memory is provided.
module tensorforge_multitile_top #(
    parameter int N = 4,
    parameter int K_MAX = 32,
    parameter int ACC_W = 32,
    parameter int ADDR_W = $clog2(N*K_MAX)
) (
    input logic clk, rst_n,
    input logic configure,
    input logic [15:0] requested_tiles,
    input logic tile_ready,
    input logic enable,
    input logic mode_int4,
    input logic [$clog2(K_MAX+1)-1:0] k_len,
    input logic a_write, b_write,
    input logic [ADDR_W-1:0] write_addr,
    input logic [7:0] write_data,
    output logic busy, done, active_bank,
    output logic running, all_done, ready_pending,
    output logic [15:0] launched_tiles, completed_tiles,
    output logic [31:0] cycle_count, stall_count,
    output logic [N*N*ACC_W-1:0] results,
    input logic [15:0] m_dim, p_dim, tile_row, tile_col,
    input logic first_k_block,
    input logic [15:0] read_row, read_col,
    output logic [ACC_W-1:0] read_data,
    output logic read_valid, writeback_busy,
    output logic [31:0] accepted_writes
);
    logic launch, scheduler_done, wb_valid, wb_first, wb_finished, wb_accepted;
    logic [15:0] launched_row, launched_col, wb_row, wb_col;
    logic [$clog2(N)-1:0] wb_row_lane, wb_col_lane;
    logic [ACC_W-1:0] wb_data;
    assign all_done = scheduler_done && !writeback_busy;
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            launched_row <= '0;
            launched_col <= '0;
        end else if (launch) begin
            launched_row <= tile_row;
            launched_col <= tile_col;
        end
    end
    multi_tile_scheduler scheduler (
        .clk(clk), .rst_n(rst_n),
        .configure(configure), .requested_tiles(requested_tiles),
        .tile_ready(tile_ready), .engine_busy(busy || writeback_busy), .engine_done(done),
        .engine_start(launch), .running(running), .all_done(scheduler_done),
        .launched_tiles(launched_tiles), .completed_tiles(completed_tiles),
        .ready_pending(ready_pending)
    );
    tile_writeback_sequencer #(.N(N), .ACC_W(ACC_W)) writeback (
        .clk(clk), .rst_n(rst_n), .engine_done(done),
        .engine_results(results), .tile_row(launched_row),
        .tile_col(launched_col), .first_k_block(first_k_block),
        .busy(writeback_busy), .write_valid(wb_valid),
        .write_tile_row(wb_row), .write_tile_col(wb_col),
        .write_first_k_block(wb_first),
        .write_row_lane(wb_row_lane), .write_col_lane(wb_col_lane),
        .write_partial_sum(wb_data), .transfer_done(wb_finished)
    );
    output_accumulator #(.N(N), .ACC_W(ACC_W)) output_store (
        .clk(clk), .rst_n(rst_n), .m_dim(m_dim), .p_dim(p_dim),
        .write_valid(wb_valid), .first_k_block(wb_first),
        .tile_row(wb_row), .tile_col(wb_col),
        .row_lane(wb_row_lane), .col_lane(wb_col_lane),
        .partial_sum(wb_data), .write_accepted(wb_accepted),
        .read_row(read_row), .read_col(read_col),
        .read_data(read_data), .read_valid(read_valid),
        .accepted_writes(accepted_writes)
    );
    double_buffered_tile_engine #(.N(N), .K_MAX(K_MAX), .ACC_W(ACC_W)) engine (
        .clk(clk), .rst_n(rst_n), .start(launch), .enable(enable),
        .mode_int4(mode_int4), .k_len(k_len),
        .a_write(a_write), .b_write(b_write),
        .write_addr(write_addr), .write_data(write_data),
        .busy(busy), .done(done), .active_bank(active_bank),
        .cycle_count(cycle_count), .stall_count(stall_count),
        .results(results)
    );
endmodule

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
    output logic [N*N*ACC_W-1:0] results
);
    logic launch;
    multi_tile_scheduler scheduler (
        .clk(clk), .rst_n(rst_n),
        .configure(configure), .requested_tiles(requested_tiles),
        .tile_ready(tile_ready), .engine_busy(busy), .engine_done(done),
        .engine_start(launch), .running(running), .all_done(all_done),
        .launched_tiles(launched_tiles), .completed_tiles(completed_tiles),
        .ready_pending(ready_pending)
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

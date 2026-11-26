// Autonomous operand staging from one-cycle registered row-major SRAM.
// Host supplies A/B source read data, not per-tile writes or ready pulses.
module tensorforge_handshake_top #(
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
    input logic a_req_ready, b_req_ready, a_rsp_valid, b_rsp_valid,
    output logic a_rsp_ready, b_rsp_ready,
    input logic [15:0] read_row, read_col,
    output logic [ACC_W-1:0] read_data,
    output logic read_valid, job_done,
    output logic loader_busy, engine_busy, writeback_busy,
    output logic [31:0] tiles_visited, accepted_writes,
    output logic [31:0] overlap_cycles
);
    logic engine_start, engine_done, writeback_done;
    logic [N*N*ACC_W-1:0] results;

    logic wb_valid, wb_first;
    logic [15:0] wb_row, wb_col;
    logic [$clog2(N)-1:0] wb_row_lane, wb_col_lane;
    logic [ACC_W-1:0] wb_data;
    logic [15:0] launched_row, launched_col;
    logic launched_first;
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            launched_row <= '0;
            launched_col <= '0;
            launched_first <= 1'b0;
        end else if (engine_start) begin
            launched_row <= tile_row;
            launched_col <= tile_col;
            launched_first <= first_k_block;
        end
    end

    logic [15:0] tile_row, tile_col, k_block;
    logic [$clog2(K_MAX+1)-1:0] current_k_len;
    logic first_k_block, iterator_active, iterator_done;
    logic load_start, load_done, staged, running, inflight;
    logic a_write, b_write;
    logic [ADDR_W-1:0] write_addr;
    logic [7:0] write_data;
    logic accept_start, wb_done_d;
    logic [15:0] job_m, job_k, job_p;
    logic job_mode;
    assign accept_start = start && !running;
    assign load_start = running && iterator_active && !staged && !loader_busy && !load_done;
    // Launch only after all writes drain and previous writeback finishes.
    assign engine_start = running && staged && !inflight && !engine_busy && !loader_busy;
    assign job_done = !running && iterator_done;
    matrix_tile_iterator #(.N(N), .K_TILE(K_MAX)) iterator (
        .clk(clk), .rst_n(rst_n), .start(accept_start),
        .tile_advance(engine_start), .m_dim(m_dim), .k_dim(k_dim), .p_dim(p_dim),
        .active(iterator_active), .done(iterator_done), .tile_row(tile_row),
        .tile_col(tile_col), .k_block(k_block), .current_k_len(current_k_len),
        .first_k_block(first_k_block), .last_k_block(), .tiles_visited(tiles_visited)
    );
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            staged <= 0; running <= 0; inflight <= 0; wb_done_d <= 0;
            overlap_cycles <= 0; job_m <= 0; job_k <= 0; job_p <= 0; job_mode <= 0;
        end else begin
            wb_done_d <= writeback_done;
            if (accept_start) begin
                running <= 1; staged <= 0; inflight <= 0; overlap_cycles <= 0;
                job_m <= m_dim; job_k <= k_dim; job_p <= p_dim; job_mode <= mode_int4;
            end else if (running) begin
                if (load_done) staged <= 1;
                if (engine_start) begin staged <= 0; inflight <= 1; end
                if (writeback_done && !wb_done_d) inflight <= 0;
                if (iterator_done && !inflight) running <= 0;
                if (loader_busy && engine_busy) overlap_cycles <= overlap_cycles + 1;
            end
        end
    end
    matrix_operand_loader_handshake #(.N(N), .K_TILE(K_MAX), .ADDR_W(ADDR_W)) loader (
        .clk(clk), .rst_n(rst_n), .start(load_start),
        .m_dim(job_m), .k_dim(job_k), .p_dim(job_p),
        .tile_row(tile_row), .tile_col(tile_col), .k_block(k_block),
        .current_k_len(current_k_len), .busy(loader_busy), .done(load_done),
        .a_write(a_write), .b_write(b_write), .write_addr(write_addr),
        .write_data(write_data), .a_read(a_read), .b_read(b_read),
        .a_read_addr(a_read_addr), .b_read_addr(b_read_addr),
        .a_read_data(a_read_data), .b_read_data(b_read_data),
        .a_req_ready(a_req_ready), .b_req_ready(b_req_ready),
        .a_rsp_valid(a_rsp_valid), .b_rsp_valid(b_rsp_valid),
        .a_rsp_ready(a_rsp_ready), .b_rsp_ready(b_rsp_ready)
    );
    double_buffered_tile_engine #(.N(N), .K_MAX(K_MAX), .ACC_W(ACC_W)) engine (
        .clk(clk), .rst_n(rst_n), .start(engine_start),
        .enable(enable), .mode_int4(job_mode), .k_len(current_k_len),
        .a_write(a_write), .b_write(b_write),
        .write_addr(write_addr), .write_data(write_data),
        .busy(engine_busy), .done(engine_done), .active_bank(),
        .cycle_count(), .stall_count(),
        .results(results)
    );
    tile_writeback_sequencer #(.N(N), .ACC_W(ACC_W)) serializer (
        .clk(clk), .rst_n(rst_n), .engine_done(engine_done),
        .engine_results(results), .tile_row(launched_row),
        .tile_col(launched_col), .first_k_block(launched_first),
        .busy(writeback_busy), .write_valid(wb_valid),
        .write_tile_row(wb_row), .write_tile_col(wb_col),
        .write_first_k_block(wb_first),
        .write_row_lane(wb_row_lane), .write_col_lane(wb_col_lane),
        .write_partial_sum(wb_data), .transfer_done(writeback_done)
    );
    output_accumulator #(.N(N), .ACC_W(ACC_W)) output_store (
        .clk(clk), .rst_n(rst_n), .m_dim(job_m), .p_dim(job_p),
        .write_valid(wb_valid), .first_k_block(wb_first),
        .tile_row(wb_row), .tile_col(wb_col),
        .row_lane(wb_row_lane), .col_lane(wb_col_lane),
        .partial_sum(wb_data), .write_accepted(),
        .read_row(read_row), .read_col(read_col),
        .read_data(read_data), .read_valid(read_valid),
        .accepted_writes(accepted_writes)
    );
endmodule

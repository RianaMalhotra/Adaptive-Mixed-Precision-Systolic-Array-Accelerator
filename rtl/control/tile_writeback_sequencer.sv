// Serializes a completed N x N tile into N*N accumulator writes.
// Capture is on the rising edge of engine_done; outputs remain stable
// throughout the transfer even if the engine result bus changes.
module tile_writeback_sequencer #(
    parameter int N = 4,
    parameter int ACC_W = 32,
    parameter int IDX_W = 16
) (
    input logic clk, rst_n,
    input logic engine_done,
    input logic [N*N*ACC_W-1:0] engine_results,
    input logic [IDX_W-1:0] tile_row, tile_col,
    input logic first_k_block,
    output logic busy,
    output logic write_valid,
    output logic [IDX_W-1:0] write_tile_row, write_tile_col,
    output logic write_first_k_block,
    output logic [$clog2(N)-1:0] write_row_lane, write_col_lane,
    output logic [ACC_W-1:0] write_partial_sum,
    output logic transfer_done
);
    localparam int COUNT_W = $clog2(N*N+1);
    logic [COUNT_W-1:0] index;
    logic done_d;
    logic [N*N*ACC_W-1:0] snapshot;
    assign write_valid = busy;
    assign write_row_lane = ($clog2(N))'(index / N);
    assign write_col_lane = ($clog2(N))'(index % N);
    assign write_partial_sum = snapshot[(index*ACC_W) +: ACC_W];
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            busy <= 1'b0;
            index <= '0;
            done_d <= 1'b0;
            snapshot <= '0;
            write_tile_row <= '0;
            write_tile_col <= '0;
            write_first_k_block <= 1'b0;
            transfer_done <= 1'b0;
        end else begin
            done_d <= engine_done;
            transfer_done <= 1'b0;
            if (!busy && engine_done && !done_d) begin
                snapshot <= engine_results;
                write_tile_row <= tile_row;
                write_tile_col <= tile_col;
                write_first_k_block <= first_k_block;
                index <= '0;
                busy <= 1'b1;
            end else if (busy) begin
                if (index == COUNT_W'(N*N-1)) begin
                    busy <= 1'b0;
                    transfer_done <= 1'b1;
                end else
                    index <= index + 1'b1;
            end
        end
    end
endmodule

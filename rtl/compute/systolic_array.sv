// Wavefront-fed output-stationary array.
// Feed row r of A delayed by r cycles and column c of B delayed by c cycles.
// Input lane data must be zero when its lane is invalid; valid propagation
// is implicit in the zero-padded wavefront. clear begins a new output tile.
module systolic_array #(
    parameter int N = 4,
    parameter int ACC_W = 32
) (
    input logic clk,
    input logic rst_n,
    input logic clear,
    input logic enable,
    input logic mode_int4,
    input logic signed [N*8-1:0] a_rows,
    input logic signed [N*8-1:0] b_cols,
    output logic signed [N*N*ACC_W-1:0] accumulators
);
    wire signed [7:0] a_pipe [0:N-1][0:N];
    wire signed [7:0] b_pipe [0:N][0:N-1];
    wire valid_unused [0:N-1][0:N-1];
    for (genvar r=0; r<N; r++) begin : rows
        assign a_pipe[r][0] = a_rows[r*8 +: 8];
        for (genvar c=0; c<N; c++) begin : cols
            if (r == 0)
                assign b_pipe[0][c] = b_cols[c*8 +: 8];
            mixed_precision_pe #(.ACC_W(ACC_W)) pe (
                .clk(clk), .rst_n(rst_n), .clear(clear), .enable(enable),
                .mode_int4(mode_int4), .a_in(a_pipe[r][c]),
                .b_in(b_pipe[r][c]), .valid_in(1'b1),
                .a_out(a_pipe[r][c+1]), .b_out(b_pipe[r+1][c]),
                .valid_out(valid_unused[r][c]),
                .accumulator(accumulators[(r*N+c)*ACC_W +: ACC_W])
            );
        end
    end
endmodule

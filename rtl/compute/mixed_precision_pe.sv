// TensorForge output-stationary processing element.
// INT8: one signed product/cycle. INT4: two packed signed products/cycle.
module mixed_precision_pe #(
    parameter int ACC_W = 32
) (
    input  logic clk,
    input  logic rst_n,
    input  logic clear,
    input  logic enable,
    input  logic mode_int4,
    input  logic signed [7:0] a_in,
    input  logic signed [7:0] b_in,
    input  logic valid_in,
    output logic signed [7:0] a_out,
    output logic signed [7:0] b_out,
    output logic valid_out,
    output logic signed [ACC_W-1:0] accumulator
);
    logic signed [3:0] a_lo, a_hi, b_lo, b_hi;
    logic signed [15:0] product8;
    logic signed [8:0] product4_sum;
    logic signed [ACC_W-1:0] contribution;
    always_comb begin
        a_lo = $signed(a_in[3:0]);
        a_hi = $signed(a_in[7:4]);
        b_lo = $signed(b_in[3:0]);
        b_hi = $signed(b_in[7:4]);
        product8 = a_in * b_in;
        product4_sum = ($signed(a_lo) * $signed(b_lo)) +
                       ($signed(a_hi) * $signed(b_hi));
        contribution = mode_int4 ? {{(ACC_W-9){product4_sum[8]}}, product4_sum}
                                 : {{(ACC_W-16){product8[15]}}, product8};
    end
`ifndef SYNTHESIS
    initial assert (ACC_W >= 16) else $fatal(1, "ACC_W must be >= 16");
`endif
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            a_out <= '0;
            b_out <= '0;
            valid_out <= 1'b0;
            accumulator <= '0;
        end else if (clear) begin
            a_out <= '0;
            b_out <= '0;
            valid_out <= 1'b0;
            accumulator <= '0;
        end else if (enable) begin
            a_out <= a_in;
            b_out <= b_in;
            valid_out <= valid_in;
            if (valid_in)
                accumulator <= accumulator + contribution;
        end
    end
endmodule

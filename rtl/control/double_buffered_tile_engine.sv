// TensorForge M3: programmable reduction-length output tile.
// Host writes packed A[row,k] and B[k,col] bytes into separate stores.
// A and B are row-major with strides K_MAX and N respectively.
// start launches one N x N output tile; enable stalls the whole wavefront.
// Writes target the inactive bank, including during compute. mode_int4 is sampled on start.
// Results remain readable until the next start. done is sticky until start.
module double_buffered_tile_engine #(
    parameter int N = 4,
    parameter int K_MAX = 32,
    parameter int ACC_W = 32,
    parameter int ADDR_W = $clog2(N*K_MAX)
) (
    input logic clk, rst_n,
    input logic start,
    input logic enable,
    input logic mode_int4,
    input logic [$clog2(K_MAX+1)-1:0] k_len,
    input logic a_write, b_write,
    input logic [ADDR_W-1:0] write_addr,
    input logic [7:0] write_data,
    output logic busy, done,
    output logic active_bank,
    output logic [31:0] cycle_count,
    output logic [31:0] stall_count,
    output logic [N*N*ACC_W-1:0] results
);
    localparam int CW = $clog2(K_MAX+2*N+1);
    logic [7:0] a_mem [0:1][0:N*K_MAX-1];
    logic [7:0] b_mem [0:1][0:N*K_MAX-1];
    logic [CW-1:0] cycle_idx;
    logic [$clog2(K_MAX+1)-1:0] active_k;
    logic active_mode;
    logic clear_array;
    logic signed [N*8-1:0] row_lanes, col_lanes;
    logic [N*N*ACC_W-1:0] accumulators;
    logic [31:0] stall_counter, cycle_counter;
    logic [CW-1:0] last_cycle;
    assign cycle_count = cycle_counter;
    assign stall_count = stall_counter;
    assign results = accumulators;
    assign last_cycle = CW'(active_k) + CW'(2*N-2);

    always_comb begin
        row_lanes = '0;
        col_lanes = '0;
        for (int r=0; r<N; r++) begin
            if (busy && int'(cycle_idx) >= r &&
                (int'(cycle_idx)-r) < int'(active_k))
                row_lanes[r*8 +: 8] = a_mem[active_bank][r*K_MAX + int'(cycle_idx)-r];
        end
        for (int c=0; c<N; c++) begin
            if (busy && int'(cycle_idx) >= c &&
                (int'(cycle_idx)-c) < int'(active_k))
                col_lanes[c*8 +: 8] = b_mem[active_bank][(int'(cycle_idx)-c)*N+c];
        end
    end
    assign clear_array = start && !busy && k_len != 0 && int'(k_len) <= K_MAX;
    systolic_array #(.N(N), .ACC_W(ACC_W)) array (
        .clk(clk), .rst_n(rst_n), .clear(clear_array),
        .enable(enable && busy), .mode_int4(active_mode),
        .a_rows(row_lanes), .b_cols(col_lanes),
        .accumulators(accumulators)
    );
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            busy <= 1'b0;
            done <= 1'b0;
            cycle_idx <= '0;
            active_k <= '0;
            active_mode <= 1'b0;
            cycle_counter <= '0;
            stall_counter <= '0;
            active_bank <= 1'b0;
        end else begin
            if (a_write && int'(write_addr) < N*K_MAX)
                a_mem[!active_bank][write_addr] <= write_data;
            if (b_write && int'(write_addr) < N*K_MAX)
                b_mem[!active_bank][write_addr] <= write_data;
            if (!busy) begin
                if (clear_array) begin
                    active_bank <= ~active_bank;
                    busy <= 1'b1;
                    done <= 1'b0;
                    cycle_idx <= '0;
                    active_k <= k_len;
                    active_mode <= mode_int4;
                    cycle_counter <= '0;
                    stall_counter <= '0;
                end
            end else if (enable) begin
                cycle_counter <= cycle_counter + 1'b1;
                if (cycle_idx == last_cycle) begin
                    busy <= 1'b0;
                    done <= 1'b1;
                end else
                    cycle_idx <= cycle_idx + 1'b1;
            end else
                stall_counter <= stall_counter + 1'b1;
        end
    end
endmodule

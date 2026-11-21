// TensorForge DFX: result-path fault injection and comparator.
// The fault is injected into the observable result only; the original
// accumulator is retained as a reference. This is a verification/diagnostic
// mechanism, not independent redundancy against faults in the compute array.
// An injected nonzero mask on a valid sample always causes a mismatch.
// clear_status clears sticky flags/counters and has priority over sampling.
module result_fault_monitor #(
    parameter int DATA_W = 32,
    parameter int INDEX_W = 4
) (
    input logic clk, rst_n,
    input logic clear_status,
    input logic sample_valid,
    input logic [INDEX_W-1:0] sample_index,
    input logic [DATA_W-1:0] reference_result,
    input logic inject_enable,
    input logic [DATA_W-1:0] inject_mask,
    output logic [DATA_W-1:0] observed_result,
    output logic mismatch,
    output logic fault_sticky,
    output logic [INDEX_W-1:0] first_fault_index,
    output logic [31:0] sample_count,
    output logic [31:0] fault_count
);
    assign observed_result = reference_result ^
        (inject_enable ? inject_mask : {DATA_W{1'b0}});
    assign mismatch = sample_valid && (observed_result != reference_result);
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            fault_sticky <= 1'b0;
            first_fault_index <= '0;
            sample_count <= '0;
            fault_count <= '0;
        end else if (clear_status) begin
            fault_sticky <= 1'b0;
            first_fault_index <= '0;
            sample_count <= '0;
            fault_count <= '0;
        end else if (sample_valid) begin
            sample_count <= sample_count + 1'b1;
            if (mismatch) begin
                fault_count <= fault_count + 1'b1;
                if (!fault_sticky)
                    first_fault_index <= sample_index;
                fault_sticky <= 1'b1;
            end
        end
    end
endmodule

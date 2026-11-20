// Behavioral synthesizable single-write / combinational-read tile store.
// A future FPGA/ASIC backend can replace this with a technology SRAM macro.
module tile_sram #(
    parameter int DEPTH = 128,
    parameter int ADDR_W = $clog2(DEPTH)
) (
    input logic clk,
    input logic write_en,
    input logic [ADDR_W-1:0] write_addr,
    input logic [7:0] write_data,
    input logic [ADDR_W-1:0] read_addr,
    output logic [7:0] read_data
);
    logic [7:0] mem [0:DEPTH-1];
    always_ff @(posedge clk)
        if (write_en)
            mem[write_addr] <= write_data;
    assign read_data = mem[read_addr];
endmodule

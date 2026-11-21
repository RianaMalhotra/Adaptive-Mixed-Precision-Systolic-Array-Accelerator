// Dual-bank operand buffer with independent host writes and compute reads.
// The host always writes the inactive bank, while compute reads the active bank.
// swap is accepted only when no read is requested and no host write is pending.
// A swap toggles bank ownership; the old active bank becomes writable.
// Memory contents are undefined until written. Reset changes ownership only.
module ping_pong_buffer #(
    parameter int DEPTH = 128,
    parameter int ADDR_W = $clog2(DEPTH)
) (
    input  logic clk,
    input  logic rst_n,
    input  logic swap,
    output logic swap_ready,
    output logic active_bank,
    input  logic write_valid,
    output logic write_ready,
    input  logic [ADDR_W-1:0] write_addr,
    input  logic [7:0] write_data,
    input  logic read_valid,
    output logic read_ready,
    input  logic [ADDR_W-1:0] read_addr,
    output logic [7:0] read_data,
    output logic [31:0] write_count,
    output logic [31:0] read_count,
    output logic [31:0] swap_count
);
    logic [7:0] bank0 [0:DEPTH-1];
    logic [7:0] bank1 [0:DEPTH-1];
    assign write_ready = !swap && (int'(write_addr) < DEPTH);
    assign read_ready = !swap && (int'(read_addr) < DEPTH);
    assign swap_ready = !write_valid && !read_valid;
    assign read_data = active_bank ? bank1[read_addr] : bank0[read_addr];
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            active_bank <= 1'b0;
            write_count <= '0;
            read_count <= '0;
            swap_count <= '0;
        end else begin
            if (swap && swap_ready) begin
                active_bank <= ~active_bank;
                swap_count <= swap_count + 1'b1;
            end
            if (write_valid && write_ready) begin
                if (active_bank)
                    bank0[write_addr] <= write_data;
                else
                    bank1[write_addr] <= write_data;
                write_count <= write_count + 1'b1;
            end
            if (read_valid && read_ready)
                read_count <= read_count + 1'b1;
        end
    end
endmodule

// TensorForge host register interface: one outstanding request per cycle.
// Register map (byte offsets):
// 0x00 CONTROL: bit0 START (write-one pulse), bit1 IRQ_ENABLE (RW)
// 0x04 STATUS: bit0 BUSY, bit1 DONE, bit2 IRQ_PENDING
// 0x08 CONFIG: bit0 INT4, bits15:8 K_LENGTH
// 0x0c CYCLES: enabled compute cycles
// 0x10 STALLS: stalled compute cycles
// 0x14 IRQ_ACK: write bit0 to clear pending interrupt
// 0x18 RESULT_INDEX: selects a 32-bit accumulator word
// 0x1c RESULT_DATA: selected accumulator (ACC_W=32)
// 0x20 A_ADDR: operand A address
// 0x24 A_DATA: write low byte to A SRAM while idle
// 0x28 B_ADDR: operand B address
// 0x2c B_DATA: write low byte to B SRAM while idle
// Read data and ready are combinational. Writes commit at posedge.
// start and operand write strobes are combinational pulses accepted on posedge.
module accelerator_regs #(
    parameter int N = 4,
    parameter int K_MAX = 32,
    parameter int ACC_W = 32
) (
    input logic clk, rst_n,
    input logic req_valid, req_write,
    input logic [7:0] req_addr,
    input logic [31:0] req_wdata,
    output logic req_ready,
    output logic [31:0] req_rdata,
    output logic irq
);
    localparam int ADDR_W = $clog2(N*K_MAX);
    logic irq_enable, irq_pending;
    logic mode_int4;
    logic [$clog2(K_MAX+1)-1:0] k_len;
    logic [ADDR_W-1:0] a_addr, b_addr;
    logic [$clog2(N*N)-1:0] result_index;
    logic busy, done;
    logic [31:0] cycles, stalls;
    logic [N*N*ACC_W-1:0] results;
    logic start_pulse, a_write, b_write;
    logic done_prev;
    assign req_ready = 1'b1;
    assign irq = irq_enable && irq_pending;
    assign start_pulse = req_valid && req_write && req_addr == 8'h00 && req_wdata[0] && !busy;
    assign a_write = req_valid && req_write && req_addr == 8'h24 && !busy;
    assign b_write = req_valid && req_write && req_addr == 8'h2c && !busy;
    always_comb begin
        req_rdata = '0;
        case (req_addr)
            8'h00: req_rdata = {30'b0, irq_enable, 1'b0};
            8'h04: req_rdata = {29'b0, irq_pending, done, busy};
            8'h08: req_rdata = (32'(k_len) << 8) | 32'(mode_int4);
            8'h0c: req_rdata = cycles;
            8'h10: req_rdata = stalls;
            8'h18: req_rdata = 32'(result_index);
            8'h1c: req_rdata = results[int'(result_index)*ACC_W +: 32];
            8'h20: req_rdata = 32'(a_addr);
            8'h28: req_rdata = 32'(b_addr);
            default: req_rdata = '0;
        endcase
    end
    tile_engine #(.N(N), .K_MAX(K_MAX), .ACC_W(ACC_W)) engine (
        .clk(clk), .rst_n(rst_n), .start(start_pulse), .enable(1'b1),
        .mode_int4(mode_int4), .k_len(k_len),
        .a_write(a_write), .b_write(b_write),
        .write_addr(a_write ? a_addr : b_addr),
        .write_data(req_wdata[7:0]),
        .busy(busy), .done(done), .cycle_count(cycles),
        .stall_count(stalls), .results(results)
    );
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            irq_enable <= 1'b0;
            irq_pending <= 1'b0;
            mode_int4 <= 1'b0;
            k_len <= '0;
            a_addr <= '0;
            b_addr <= '0;
            result_index <= '0;
            done_prev <= 1'b0;
        end else begin
            done_prev <= done;
            if (done && !done_prev)
                irq_pending <= 1'b1;
            if (start_pulse)
                irq_pending <= 1'b0;
            if (req_valid && req_write) begin
                case (req_addr)
                    8'h00: irq_enable <= req_wdata[1];
                    8'h08: if (!busy) begin
                        mode_int4 <= req_wdata[0];
                        k_len <= req_wdata[8 +: $clog2(K_MAX+1)];
                    end
                    8'h14: if (req_wdata[0]) irq_pending <= 1'b0;
                    8'h18: result_index <= req_wdata[$clog2(N*N)-1:0];
                    8'h20: if (!busy) a_addr <= req_wdata[ADDR_W-1:0];
                    8'h28: if (!busy) b_addr <= req_wdata[ADDR_W-1:0];
                    default: ;
                endcase
            end
        end
    end
endmodule

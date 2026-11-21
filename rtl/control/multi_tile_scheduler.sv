// TensorForge host-assisted multi-tile sequencer.
// Each tile is preloaded into the inactive bank before tile_ready is pulsed.
// The scheduler launches only when engine_busy is low and a ready credit exists.
// A credit represents ONE fully prepared tile. For two-bank storage, the host
// must not stage more than one credit at a time.
// The scheduler does not itself generate operand addresses or output writeback.
module multi_tile_scheduler #(
    parameter int COUNT_W = 16
) (
    input logic clk, rst_n,
    input logic configure,
    input logic [COUNT_W-1:0] requested_tiles,
    input logic tile_ready,
    input logic engine_busy,
    input logic engine_done,
    output logic engine_start,
    output logic running,
    output logic all_done,
    output logic [COUNT_W-1:0] launched_tiles,
    output logic [COUNT_W-1:0] completed_tiles,
    output logic ready_pending
);
    logic done_prev;
    logic [COUNT_W-1:0] target_tiles;
    logic completion_event;
    assign completion_event = engine_done && !done_prev && running;
    assign engine_start = running && !engine_busy && ready_pending &&
                          launched_tiles < target_tiles && !completion_event;
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            running <= 1'b0;
            all_done <= 1'b0;
            launched_tiles <= '0;
            completed_tiles <= '0;
            target_tiles <= '0;
            ready_pending <= 1'b0;
            done_prev <= 1'b0;
        end else begin
            done_prev <= engine_done;
            if (configure && !running) begin
                target_tiles <= requested_tiles;
                running <= (requested_tiles != 0);
                all_done <= (requested_tiles == 0);
                launched_tiles <= '0;
                completed_tiles <= '0;
                ready_pending <= 1'b0;
            end else if (running) begin
                if (tile_ready && !ready_pending && !engine_start)
                    ready_pending <= 1'b1;
                if (engine_start) begin
                    launched_tiles <= launched_tiles + 1'b1;
                    ready_pending <= 1'b0;
                end
                if (completion_event) begin
                    completed_tiles <= completed_tiles + 1'b1;
                    if (completed_tiles + 1'b1 == target_tiles) begin
                        running <= 1'b0;
                        all_done <= 1'b1;
                    end
                end
            end
        end
    end
endmodule

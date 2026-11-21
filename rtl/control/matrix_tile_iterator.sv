// Autonomous tile-coordinate iterator for C[M,P] += A[M,K]*B[K,P].
// Coordinates enumerate reduction blocks fastest, then output columns,
// then output rows. A tile_advance pulse consumes the current coordinate.
// No memory transactions are issued by this standalone controller.
module matrix_tile_iterator #(
    parameter int N = 4,
    parameter int K_TILE = 32,
    parameter int IDX_W = 16
) (
    input logic clk, rst_n,
    input logic start,
    input logic tile_advance,
    input logic [IDX_W-1:0] m_dim, k_dim, p_dim,
    output logic active, done,
    output logic [IDX_W-1:0] tile_row, tile_col, k_block,
    output logic [$clog2(K_TILE+1)-1:0] current_k_len,
    output logic first_k_block, last_k_block,
    output logic [31:0] tiles_visited
);
    logic [IDX_W-1:0] row_limit, col_limit, k_limit;
    logic [IDX_W-1:0] k_latched;
    logic [IDX_W-1:0] remaining;
    assign first_k_block = (k_block == 0);
    assign last_k_block = (k_block + 1'b1 == k_limit);
    assign remaining = k_latched - IDX_W'(k_block*K_TILE);
    assign current_k_len = (32'(remaining) >= K_TILE) ?
        ($clog2(K_TILE+1))'(K_TILE) :
        ($clog2(K_TILE+1))'(remaining);
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            active <= 1'b0;
            done <= 1'b0;
            tile_row <= '0;
            tile_col <= '0;
            k_block <= '0;
            row_limit <= '0;
            col_limit <= '0;
            k_limit <= '0;
            k_latched <= '0;
            tiles_visited <= '0;
        end else if (start && !active) begin
            row_limit <= IDX_W'((32'(m_dim) + N - 1) / N);
            col_limit <= IDX_W'((32'(p_dim) + N - 1) / N);
            k_limit <= IDX_W'((32'(k_dim) + K_TILE - 1) / K_TILE);
            k_latched <= k_dim;
            tile_row <= '0;
            tile_col <= '0;
            k_block <= '0;
            tiles_visited <= '0;
            active <= (m_dim != 0 && k_dim != 0 && p_dim != 0);
            done <= (m_dim == 0 || k_dim == 0 || p_dim == 0);
        end else if (active && tile_advance) begin
            tiles_visited <= tiles_visited + 1'b1;
            if (k_block + 1'b1 < k_limit) begin
                k_block <= k_block + 1'b1;
            end else begin
                k_block <= '0;
                if (tile_col + 1'b1 < col_limit) begin
                    tile_col <= tile_col + 1'b1;
                end else begin
                    tile_col <= '0;
                    if (tile_row + 1'b1 < row_limit) begin
                        tile_row <= tile_row + 1'b1;
                    end else begin
                        active <= 1'b0;
                        done <= 1'b1;
                    end
                end
            end
        end
    end
endmodule

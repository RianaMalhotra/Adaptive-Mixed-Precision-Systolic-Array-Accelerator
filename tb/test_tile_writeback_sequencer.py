import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def capture_and_serialize_two_tiles(dut):
    n = 4
    dut.rst_n.value = 0
    dut.engine_done.value = 0
    dut.engine_results.value = 0
    dut.tile_row.value = 0
    dut.tile_col.value = 0
    dut.first_k_block.value = 0
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    async def tick():
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

    await tick()
    dut.rst_n.value = 1
    for tile in range(2):
        values = [((tile+1)*100+i) for i in range(n*n)]
        dut.engine_results.value = sum(v << (i*32) for i,v in enumerate(values))
        dut.tile_row.value = tile
        dut.tile_col.value = 1
        dut.first_k_block.value = int(tile==0)
        dut.engine_done.value = 1
        await tick()
        assert int(dut.busy.value) == 1
        dut.engine_results.value = 0
        dut.tile_row.value = 99
        dut.tile_col.value = 99
        for i in range(n*n):
            assert int(dut.write_valid.value) == 1
            assert int(dut.write_row_lane.value) == i//n
            assert int(dut.write_col_lane.value) == i%n
            assert int(dut.write_partial_sum.value) == values[i]
            assert int(dut.write_tile_row.value) == tile
            assert int(dut.write_tile_col.value) == 1
            assert int(dut.write_first_k_block.value) == int(tile==0)
            await tick()
        assert int(dut.busy.value) == 0
        assert int(dut.transfer_done.value) == 1
        dut.engine_done.value = 0
        await tick()
        assert int(dut.transfer_done.value) == 0

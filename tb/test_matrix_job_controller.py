import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def job_waits_for_operands_engine_and_writeback(dut):
    dut.rst_n.value = 0
    dut.start.value = 0
    dut.m_dim.value = 5
    dut.k_dim.value = 33
    dut.p_dim.value = 5
    dut.operands_ready.value = 0
    dut.engine_busy.value = 0
    dut.engine_done.value = 0
    dut.writeback_done.value = 0
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    async def tick():
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

    await tick()
    dut.rst_n.value = 1
    dut.start.value = 1
    await tick()
    dut.start.value = 0
    expected = [(r,c,b,32 if b==0 else 1)
                for r in range(2) for c in range(2) for b in range(2)]
    for index,(r,c,b,k) in enumerate(expected):
        assert int(dut.waiting_for_operands.value) == 1
        assert (int(dut.tile_row.value),int(dut.tile_col.value),
                int(dut.k_block.value),int(dut.current_k_len.value)) == (r,c,b,k)
        for _ in range(3):
            await tick()
            assert int(dut.engine_start.value) == 0
        dut.operands_ready.value = 1
        await tick()
        dut.operands_ready.value = 0
        assert int(dut.engine_start.value) == 1
        await tick()
        assert int(dut.waiting_for_engine.value) == 1
        for _ in range(3):
            await tick()
            assert int(dut.tiles_visited.value) == index
        dut.engine_done.value = 1
        await tick()
        dut.engine_done.value = 0
        assert int(dut.waiting_for_writeback.value) == 1
        for _ in range(3):
            await tick()
            assert int(dut.tiles_visited.value) == index
        dut.writeback_done.value = 1
        await tick()
        dut.writeback_done.value = 0
        await tick()
        await tick()
    assert int(dut.tiles_visited.value) == len(expected)
    assert int(dut.job_done.value) == 1

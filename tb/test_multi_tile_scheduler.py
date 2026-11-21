import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def schedule_three_tiles_with_waits(dut):
    dut.rst_n.value = 0
    dut.configure.value = 0
    dut.requested_tiles.value = 0
    dut.tile_ready.value = 0
    dut.engine_busy.value = 0
    dut.engine_done.value = 0
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    async def tick():
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

    await tick()
    dut.rst_n.value = 1
    dut.requested_tiles.value = 3
    dut.configure.value = 1
    await tick()
    dut.configure.value = 0
    assert int(dut.running.value) == 1

    for i in range(3):
        # Delayed host tile preparation: no speculative launches.
        for _ in range(4):
            assert int(dut.engine_start.value) == 0
            await tick()
        dut.tile_ready.value = 1
        await tick()
        dut.tile_ready.value = 0
        await Timer(1, units="ns")
        assert int(dut.ready_pending.value) == 1
        assert int(dut.engine_start.value) == 1
        # Model engine latching start on the next edge.
        await tick()
        dut.engine_busy.value = 1
        dut.engine_done.value = 0
        assert int(dut.launched_tiles.value) == i+1
        assert int(dut.ready_pending.value) == 0
        for _ in range(6):
            assert int(dut.engine_start.value) == 0
            await tick()
        dut.engine_busy.value = 0
        dut.engine_done.value = 1
        await tick()
        assert int(dut.completed_tiles.value) == i+1
        dut.engine_done.value = 0
        await tick()
    assert int(dut.running.value) == 0
    assert int(dut.all_done.value) == 1
    assert int(dut.launched_tiles.value) == 3
    assert int(dut.completed_tiles.value) == 3
    assert int(dut.engine_start.value) == 0

    # Zero-tile command completes immediately.
    dut.requested_tiles.value = 0
    dut.configure.value = 1
    await tick()
    assert int(dut.all_done.value) == 1
    assert int(dut.running.value) == 0

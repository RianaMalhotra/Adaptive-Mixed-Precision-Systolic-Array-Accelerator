import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def traversal_and_partial_reduction(dut):
    dut.rst_n.value = 0
    dut.start.value = 0
    dut.tile_advance.value = 0
    dut.m_dim.value = 0
    dut.k_dim.value = 0
    dut.p_dim.value = 0
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    async def tick():
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

    await tick()
    dut.rst_n.value = 1
    for m,k,p in [(5,65,7),(4,32,4),(1,1,1),(9,33,2),(0,4,4)]:
        dut.m_dim.value = m
        dut.k_dim.value = k
        dut.p_dim.value = p
        dut.start.value = 1
        await tick()
        dut.start.value = 0
        expected = [
            (r,c,b,min(32,k-b*32))
            for r in range((m+3)//4)
            for c in range((p+3)//4)
            for b in range((k+31)//32)
        ]
        if not expected:
            assert int(dut.done.value) == 1
            assert int(dut.active.value) == 0
            continue
        for i,(r,c,b,remaining) in enumerate(expected):
            assert int(dut.active.value) == 1
            assert int(dut.tile_row.value) == r
            assert int(dut.tile_col.value) == c
            assert int(dut.k_block.value) == b
            assert int(dut.current_k_len.value) == remaining
            assert int(dut.first_k_block.value) == int(b==0)
            assert int(dut.last_k_block.value) == int(b==(k+31)//32-1)
            # No progress without handshake.
            await tick()
            assert int(dut.tiles_visited.value) == i
            dut.tile_advance.value = 1
            await tick()
            dut.tile_advance.value = 0
        assert int(dut.done.value) == 1
        assert int(dut.active.value) == 0
        assert int(dut.tiles_visited.value) == len(expected)

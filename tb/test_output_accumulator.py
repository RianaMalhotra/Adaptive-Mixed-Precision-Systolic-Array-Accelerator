import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def reduction_block_accumulation_and_edge_masks(dut):
    rng = random.Random(927)
    dut.rst_n.value = 0
    dut.m_dim.value = 7
    dut.p_dim.value = 6
    dut.write_valid.value = 0
    dut.first_k_block.value = 0
    dut.tile_row.value = 0
    dut.tile_col.value = 0
    dut.row_lane.value = 0
    dut.col_lane.value = 0
    dut.partial_sum.value = 0
    dut.read_row.value = 0
    dut.read_col.value = 0
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    async def tick():
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

    await tick()
    dut.rst_n.value = 1
    expected = [[0]*6 for _ in range(7)]
    accepted = 0
    for kb in range(3):
        for tr in range(2):
            for tc in range(2):
                for r in range(4):
                    for c in range(4):
                        gr, gc = tr*4+r, tc*4+c
                        value = rng.randrange(-2000,2001)
                        dut.tile_row.value = tr
                        dut.tile_col.value = tc
                        dut.row_lane.value = r
                        dut.col_lane.value = c
                        dut.partial_sum.value = value & 0xffffffff
                        dut.first_k_block.value = int(kb == 0)
                        dut.write_valid.value = 1
                        await Timer(1, units="ns")
                        assert int(dut.write_accepted.value) == int(gr<7 and gc<6)
                        await tick()
                        if gr<7 and gc<6:
                            accepted += 1
                            expected[gr][gc] = (value if kb==0 else expected[gr][gc]+value) & 0xffffffff
    dut.write_valid.value = 0
    assert int(dut.accepted_writes.value) == accepted
    for r in range(7):
        for c in range(6):
            dut.read_row.value = r
            dut.read_col.value = c
            await Timer(1, units="ns")
            assert int(dut.read_valid.value) == 1
            assert int(dut.read_data.value) == expected[r][c]
    dut.read_row.value = 7
    await Timer(1, units="ns")
    assert int(dut.read_valid.value) == 0
    assert int(dut.read_data.value) == 0

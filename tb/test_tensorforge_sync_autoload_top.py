import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def autoload_signed_int8_matrix(dut):
    m, k, p = 5, 33, 5
    a = [((r*3+t)%11)-5 for r in range(m) for t in range(k)]
    b = [((t*2+c)%9)-4 for t in range(k) for c in range(p)]
    dut.rst_n.value = 0
    dut.start.value = 0
    dut.enable.value = 1
    dut.mode_int4.value = 0
    dut.m_dim.value = m
    dut.k_dim.value = k
    dut.p_dim.value = p
    dut.a_read_data.value = 0
    dut.b_read_data.value = 0
    dut.read_row.value = 0
    dut.read_col.value = 0
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    async def tick():
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

    async def drive_sources():
        while True:
            # Model a one-cycle registered SRAM: sample request at rising edge.
            await Timer(1, units="ns")
            ai = int(dut.a_read_addr.value)
            bi = int(dut.b_read_addr.value)
            ar = int(dut.a_read.value)
            br = int(dut.b_read.value)
            await RisingEdge(dut.clk)
            if ar:
                dut.a_read_data.value = a[ai] & 255
            if br:
                dut.b_read_data.value = b[bi] & 255
            await Timer(1, units="ns")

    cocotb.start_soon(drive_sources())
    await tick()
    dut.rst_n.value = 1
    dut.start.value = 1
    await tick()
    dut.start.value = 0
    for _ in range(3500):
        await tick()
        if int(dut.job_done.value):
            break
    else:
        assert False, "autonomous job timed out"
    assert int(dut.tiles_visited.value) == 8
    assert int(dut.accepted_writes.value) == 2*m*p
    for r in range(m):
        for c in range(p):
            dut.read_row.value = r
            dut.read_col.value = c
            await Timer(1, units="ns")
            got = int(dut.read_data.value)
            if got >= 2**31:
                got -= 2**32
            expected = sum(a[r*k+t]*b[t*p+c] for t in range(k))
            assert int(dut.read_valid.value) == 1
            assert got == expected, (r,c,got,expected)

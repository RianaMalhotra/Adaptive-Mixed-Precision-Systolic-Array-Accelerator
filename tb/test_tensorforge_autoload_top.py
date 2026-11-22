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
            await Timer(1, units="ns")
            ai = int(dut.a_read_addr.value)
            bi = int(dut.b_read_addr.value)
            dut.a_read_data.value = a[ai] & 255 if int(dut.a_read.value) else 0
            dut.b_read_data.value = b[bi] & 255 if int(dut.b_read.value) else 0
            await Timer(1, units="ns")

    cocotb.start_soon(drive_sources())
    await tick()
    dut.rst_n.value = 1
    dut.start.value = 1
    await tick()
    dut.start.value = 0
    for elapsed_cycles in range(1, 3501):
        await tick()
        if int(dut.job_done.value):
            break
    else:
        assert False, "autonomous job timed out"
    # Count useful scalar MACs, excluding padded lanes and tile cells.
    useful_macs = 1 * m * k * p
    dut._log.info("BENCH memory=combinational precision=INT8 cycles=%d useful_macs=%d mac_per_cycle=%.6f",
                  elapsed_cycles, useful_macs, useful_macs / elapsed_cycles)
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


@cocotb.test()
async def autoload_packed_signed_int4_matrix(dut):
    # Two signed nibble lanes per byte; verify both lanes' dot products.
    m, k, p = 5, 33, 5

    def pack(lo, hi):
        return (lo & 15) | ((hi & 15) << 4)

    def unpack(v):
        lo, hi = v & 15, (v >> 4) & 15
        return (lo - 16 if lo >= 8 else lo,
                hi - 16 if hi >= 8 else hi)

    a = [pack(((r*3+t)%16)-8, ((r+t*5)%16)-8)
         for r in range(m) for t in range(k)]
    b = [pack(((t*2+c)%16)-8, ((t+c*3)%16)-8)
         for t in range(k) for c in range(p)]
    dut.rst_n.value = 0
    dut.start.value = 0
    dut.enable.value = 1
    dut.mode_int4.value = 1
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
            await Timer(1, units="ns")
            ai = int(dut.a_read_addr.value)
            bi = int(dut.b_read_addr.value)
            dut.a_read_data.value = a[ai] & 255 if int(dut.a_read.value) else 0
            dut.b_read_data.value = b[bi] & 255 if int(dut.b_read.value) else 0
            await Timer(1, units="ns")

    cocotb.start_soon(drive_sources())
    await tick()
    dut.rst_n.value = 1
    dut.start.value = 1
    await tick()
    dut.start.value = 0
    for elapsed_cycles in range(1, 3501):
        await tick()
        if int(dut.job_done.value):
            break
    else:
        assert False, "synchronous SRAM INT4 matrix job timed out"

    # Count useful scalar MACs, excluding padded lanes and tile cells.
    useful_macs = 2 * m * k * p
    dut._log.info("BENCH memory=combinational precision=INT4 cycles=%d useful_macs=%d mac_per_cycle=%.6f",
                  elapsed_cycles, useful_macs, useful_macs / elapsed_cycles)
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
            expected = sum(
                unpack(a[r*k+t])[0]*unpack(b[t*p+c])[0] +
                unpack(a[r*k+t])[1]*unpack(b[t*p+c])[1]
                for t in range(k)
            )
            assert int(dut.read_valid.value) == 1
            assert got == expected, (r, c, got, expected)

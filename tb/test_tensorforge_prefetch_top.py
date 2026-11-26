import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def autoload_signed_int8_matrix(dut):
    m, k, p = 5, 33, 5
    rng = random.Random(42)
    a = [rng.randint(-128,127) for _ in range(m*k)]
    b = [rng.randint(-128,127) for _ in range(k*p)]
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
    for elapsed_cycles in range(1, 3501):
        await tick()
        if int(dut.job_done.value):
            break
    else:
        assert False, "autonomous job timed out"
    # Count useful scalar MACs, excluding padded lanes and tile cells.
    useful_macs = 1 * m * k * p
    dut._log.info("BENCH memory=prefetch precision=INT8 cycles=%d useful_macs=%d mac_per_cycle=%.6f",
                  elapsed_cycles, useful_macs, useful_macs / elapsed_cycles)
    assert elapsed_cycles < 2500, elapsed_cycles
    assert int(dut.overlap_cycles.value) > 0
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
            ar = int(dut.a_read.value)
            br = int(dut.b_read.value)
            await RisingEdge(dut.clk)
            if ar:
                dut.a_read_data.value = a[ai]
            if br:
                dut.b_read_data.value = b[bi]
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
    dut._log.info("BENCH memory=prefetch precision=INT4 cycles=%d useful_macs=%d mac_per_cycle=%.6f",
                  elapsed_cycles, useful_macs, useful_macs / elapsed_cycles)
    assert elapsed_cycles < 2500, elapsed_cycles
    assert int(dut.overlap_cycles.value) > 0
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


@cocotb.test()
async def randomized_boundary_and_stall_jobs(dut):
    rng = random.Random(20261126)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.start.value = 0
    dut.rst_n.value = 0
    dut.enable.value = 0
    dut.a_read_data.value = 0
    dut.b_read_data.value = 0
    dut.read_row.value = 0
    dut.read_col.value = 0

    async def tick():
        await Timer(1, units="ns")
        ar, br = int(dut.a_read.value), int(dut.b_read.value)
        ai, bi = int(dut.a_read_addr.value), int(dut.b_read_addr.value)
        await RisingEdge(dut.clk)
        if ar:
            dut.a_read_data.value = a[ai]
        if br:
            dut.b_read_data.value = b[bi]
        await Timer(1, units="ns")

    def signed(v, bits):
        return v - (1 << bits) if v & (1 << (bits-1)) else v

    a, b = [], []
    await tick()
    for m,k,p,mode in [(1,1,1,0),(4,32,4,1),(3,31,5,0),
                       (5,33,3,1),(7,65,6,0),(2,64,7,1)]:
        a = [rng.randrange(256) for _ in range(m*k)]
        b = [rng.randrange(256) for _ in range(k*p)]
        dut.rst_n.value = 0
        await tick()
        dut.rst_n.value = 1
        dut.m_dim.value, dut.k_dim.value, dut.p_dim.value = m,k,p
        dut.mode_int4.value = mode
        dut.start.value = 1
        await tick()
        dut.start.value = 0
        for cycles in range(1,20001):
            dut.enable.value = int(rng.random() >= 0.3)
            await tick()
            if int(dut.job_done.value):
                break
        else:
            assert False, "stalled matrix job timed out"
        tiles = ((m+3)//4)*((p+3)//4)*((k+31)//32)
        assert int(dut.tiles_visited.value) == tiles
        if tiles > 1:
            assert int(dut.overlap_cycles.value) > 0
        for row in range(m):
            for col in range(p):
                dut.read_row.value, dut.read_col.value = row,col
                await Timer(1, units="ns")
                expected = 0
                for t in range(k):
                    av,bv = a[row*k+t],b[t*p+col]
                    if mode:
                        expected += signed(av&15,4)*signed(bv&15,4)
                        expected += signed(av>>4,4)*signed(bv>>4,4)
                    else:
                        expected += signed(av,8)*signed(bv,8)
                assert int(dut.read_valid.value)
                assert signed(int(dut.read_data.value),32) == expected
        dut._log.info("BENCH memory=prefetch stalls=30pct mode=%d shape=%dx%dx%d cycles=%d overlap=%d",
                      mode,m,k,p,cycles,int(dut.overlap_cycles.value))

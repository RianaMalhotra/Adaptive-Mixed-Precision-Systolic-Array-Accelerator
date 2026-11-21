import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def overlapping_tile_loads(dut):
    n, kmax = 4, 32
    dut.rst_n.value = 0
    dut.start.value = 0
    dut.enable.value = 1
    dut.mode_int4.value = 0
    dut.k_len.value = 1
    dut.a_write.value = 0
    dut.b_write.value = 0
    dut.write_addr.value = 0
    dut.write_data.value = 0
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    async def tick():
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

    async def write(a, addr, value):
        dut.a_write.value = int(a)
        dut.b_write.value = int(not a)
        dut.write_addr.value = addr
        dut.write_data.value = value
        await tick()

    async def preload(a, b, k):
        for r in range(n):
            for t in range(k):
                await write(True, r*kmax+t, a[r][t])
        for t in range(k):
            for c in range(n):
                await write(False, t*n+c, b[t][c])
        dut.a_write.value = 0
        dut.b_write.value = 0

    async def launch(k, mode):
        dut.k_len.value = k
        dut.mode_int4.value = mode
        dut.start.value = 1
        await tick()
        dut.start.value = 0
        assert int(dut.busy.value) == 1

    def signed(x, bits):
        x &= (1 << bits)-1
        return x-(1 << bits) if x & (1 << (bits-1)) else x

    async def check(a, b, k, packed):
        while int(dut.busy.value):
            await tick()
        raw = int(dut.results.value)
        for r in range(n):
            for c in range(n):
                total = 0
                for t in range(k):
                    x, y = a[r][t], b[t][c]
                    if packed:
                        total += signed(x & 15,4)*signed(y & 15,4)
                        total += signed(x >> 4,4)*signed(y >> 4,4)
                    else:
                        total += signed(x,8)*signed(y,8)
                assert signed(raw >> ((r*n+c)*32),32) == total

    await tick()
    dut.rst_n.value = 1
    k = 16
    a0 = [[(r+t+1) & 127 for t in range(k)] for r in range(n)]
    b0 = [[(t+c+2) & 127 for c in range(n)] for t in range(k)]
    a1 = [[(r*3+t+2) & 15 for t in range(k)] for r in range(n)]
    b1 = [[(t*2+c+1) & 15 for c in range(n)] for t in range(k)]
    await preload(a0,b0,k)
    await launch(k,0)
    assert int(dut.active_bank.value) == 1
    # Load bank 0 during bank 1 execution. This is a genuine overlap:
    # the first tile keeps computing while host writes the next tile.
    for r in range(n):
        for t in range(k):
            await write(True,r*kmax+t,a1[r][t])
    for t in range(k):
        for c in range(n):
            await write(False,t*n+c,b1[t][c])
    dut.a_write.value = 0
    dut.b_write.value = 0
    await check(a0,b0,k,0)
    await launch(k,1)
    assert int(dut.active_bank.value) == 0
    await check(a1,b1,k,1)

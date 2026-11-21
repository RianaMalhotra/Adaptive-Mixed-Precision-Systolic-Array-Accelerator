import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def three_tiles_end_to_end(dut):
    n = 4
    dut.rst_n.value = 0
    dut.configure.value = 0
    dut.requested_tiles.value = 0
    dut.tile_ready.value = 0
    dut.enable.value = 1
    dut.mode_int4.value = 0
    dut.k_len.value = 4
    dut.a_write.value = 0
    dut.b_write.value = 0
    dut.write_addr.value = 0
    dut.write_data.value = 0
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    async def tick():
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

    async def write(is_a, address, value):
        dut.a_write.value = int(is_a)
        dut.b_write.value = int(not is_a)
        dut.write_addr.value = address
        dut.write_data.value = value
        await tick()

    async def stage(a, b, k):
        for r in range(n):
            for t in range(k):
                await write(True, r*32+t, a[r][t])
        for t in range(k):
            for c in range(n):
                await write(False, t*n+c, b[t][c])
        dut.a_write.value = 0
        dut.b_write.value = 0

    def signed(x, bits):
        x &= (1 << bits)-1
        return x-(1 << bits) if x & (1 << (bits-1)) else x

    async def verify(a, b, k, mode):
        raw = int(dut.results.value)
        for r in range(n):
            for c in range(n):
                expected = 0
                for t in range(k):
                    x, y = a[r][t], b[t][c]
                    if mode:
                        expected += signed(x&15,4)*signed(y&15,4)
                        expected += signed(x>>4,4)*signed(y>>4,4)
                    else:
                        expected += signed(x,8)*signed(y,8)
                actual = signed(raw >> ((r*n+c)*32),32)
                assert actual == expected, (r,c,actual,expected)

    await tick()
    dut.rst_n.value = 1
    dut.requested_tiles.value = 3
    dut.configure.value = 1
    await tick()
    dut.configure.value = 0
    for tile in range(3):
        mode = tile % 2
        k = 4 + tile
        a = [[(r+t+tile+1) & 15 for t in range(k)] for r in range(n)]
        b = [[(t+c+tile+2) & 15 for c in range(n)] for t in range(k)]
        await stage(a,b,k)
        dut.k_len.value = k
        dut.mode_int4.value = mode
        dut.tile_ready.value = 1
        await tick()
        dut.tile_ready.value = 0
        for _ in range(4):
            await tick()
            if int(dut.busy.value):
                break
        assert int(dut.busy.value) == 1
        assert int(dut.launched_tiles.value) == tile+1
        for _ in range(40):
            await tick()
            if int(dut.completed_tiles.value) == tile+1:
                break
        else:
            assert False, "tile completion timeout"
        await verify(a,b,k,mode)
    assert int(dut.all_done.value) == 1
    assert int(dut.launched_tiles.value) == 3
    assert int(dut.completed_tiles.value) == 3

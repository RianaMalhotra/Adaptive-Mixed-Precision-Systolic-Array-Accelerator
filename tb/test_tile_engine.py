import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


def signed(x, bits):
    x &= (1 << bits) - 1
    return x - (1 << bits) if x & (1 << (bits - 1)) else x


def mac(a, b, packed):
    if packed:
        return sum(signed(a >> s, 4) * signed(b >> s, 4) for s in (0, 4))
    return signed(a, 8) * signed(b, 8)


@cocotb.test()
async def memory_backed_tiles_with_stalls(dut):
    rng = random.Random(773)
    n = 4
    kmax = 32
    width = len(dut.results) // (n*n)
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

    await tick()
    dut.rst_n.value = 1
    for packed in (False, True):
        for k in (1, 5, 13):
            a = [[rng.randrange(256) for _ in range(k)] for _ in range(n)]
            b = [[rng.randrange(256) for _ in range(n)] for _ in range(k)]
            for r in range(n):
                for t in range(k):
                    dut.a_write.value = 1
                    dut.b_write.value = 0
                    dut.write_addr.value = r*kmax+t
                    dut.write_data.value = a[r][t]
                    await tick()
            dut.a_write.value = 0
            for t in range(k):
                for c in range(n):
                    dut.b_write.value = 1
                    dut.write_addr.value = t*n+c
                    dut.write_data.value = b[t][c]
                    await tick()
            dut.b_write.value = 0
            dut.mode_int4.value = int(packed)
            dut.k_len.value = k
            dut.start.value = 1
            await tick()
            assert int(dut.busy.value) == 1
            dut.start.value = 0
            stalls = 0
            for cyc in range(k+2*n-1):
                paused = (cyc % 4 == 1)
                dut.enable.value = int(not paused)
                if paused:
                    stalls += 1
                await tick()
            # Include all remaining cycles if stalls delayed completion.
            dut.enable.value = 1
            timeout = 0
            while int(dut.busy.value):
                await tick()
                timeout += 1
                assert timeout < k+2*n+4, "tile engine timed out"
            assert int(dut.done.value) == 1
            assert int(dut.cycle_count.value) == k+2*n-1
            assert int(dut.stall_count.value) == stalls
            raw = int(dut.results.value)
            for r in range(n):
                for c in range(n):
                    expected = sum(mac(a[r][t], b[t][c], packed) for t in range(k))
                    got = signed(raw >> ((r*n+c)*width), width)
                    assert got == expected, (packed, k, r, c, got, expected)

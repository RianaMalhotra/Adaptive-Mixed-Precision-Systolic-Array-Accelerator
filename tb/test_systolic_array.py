import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


def signed(x, bits):
    x &= (1 << bits) - 1
    return x - (1 << bits) if x & (1 << (bits - 1)) else x


def dot(a, b, packed):
    if not packed:
        return sum(signed(x, 8) * signed(y, 8) for x, y in zip(a, b))
    return sum(signed(x >> shift, 4) * signed(y >> shift, 4)
               for x, y in zip(a, b) for shift in (0, 4))


@cocotb.test()
async def randomized_tiles(dut):
    rng = random.Random(440)
    n = len(dut.a_rows) // 8
    width = len(dut.accumulators) // (n * n)
    dut.rst_n.value = 0
    dut.clear.value = 0
    dut.enable.value = 1
    dut.mode_int4.value = 0
    dut.a_rows.value = 0
    dut.b_cols.value = 0
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.rst_n.value = 1
    for packed in (False, True):
        for k in (1, 3, 9, 17):
            a = [[rng.randrange(256) for _ in range(k)] for _ in range(n)]
            b = [[rng.randrange(256) for _ in range(n)] for _ in range(k)]
            dut.clear.value = 1
            await RisingEdge(dut.clk)
            await Timer(1, unit="ns")
            dut.clear.value = 0
            dut.mode_int4.value = int(packed)
            for cycle in range(k + 2 * n - 2):
                rows = [a[r][cycle-r] if 0 <= cycle-r < k else 0 for r in range(n)]
                cols = [b[cycle-c][c] if 0 <= cycle-c < k else 0 for c in range(n)]
                dut.a_rows.value = sum(x << (8*r) for r, x in enumerate(rows))
                dut.b_cols.value = sum(x << (8*c) for c, x in enumerate(cols))
                await RisingEdge(dut.clk)
                await Timer(1, unit="ns")
            raw = int(dut.accumulators.value)
            for r in range(n):
                for c in range(n):
                    got = signed(raw >> ((r*n+c)*width), width)
                    expected = dot(a[r], [b[t][c] for t in range(k)], packed)
                    assert got == expected, (packed, k, r, c, got, expected)

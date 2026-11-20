import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


def signed(x, bits):
    x &= (1 << bits) - 1
    return x - (1 << bits) if x & (1 << (bits - 1)) else x


def contribution(a, b, packed):
    if packed:
        return sum(signed(a >> s, 4) * signed(b >> s, 4) for s in (0, 4))
    return signed(a, 8) * signed(b, 8)


@cocotb.test()
async def randomized_precision_and_stalls(dut):
    rng = random.Random(20261120)
    dut.rst_n.value = 0
    dut.clear.value = 0
    dut.enable.value = 1
    dut.mode_int4.value = 0
    dut.valid_in.value = 0
    dut.a_in.value = 0
    dut.b_in.value = 0
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.rst_n.value = 1
    expected = 0
    for i in range(500):
        a, b = rng.randrange(256), rng.randrange(256)
        packed = rng.randrange(2)
        valid = rng.randrange(2)
        enable = rng.randrange(5) != 0
        clear = i % 71 == 0
        dut.a_in.value = a
        dut.b_in.value = b
        dut.mode_int4.value = packed
        dut.valid_in.value = valid
        dut.enable.value = enable
        dut.clear.value = clear
        if clear:
            expected = 0
        elif enable and valid:
            expected = signed(expected + contribution(a, b, packed), 32)
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert signed(int(dut.accumulator.value), 32) == expected, f"iteration {i}"

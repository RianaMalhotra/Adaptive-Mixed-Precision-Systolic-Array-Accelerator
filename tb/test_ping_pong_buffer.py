import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def concurrent_load_and_consume(dut):
    rng = random.Random(9914)
    depth = 128
    model = [[None] * depth for _ in range(2)]
    active = 0
    writes = reads = swaps = 0
    dut.rst_n.value = 0
    dut.swap.value = 0
    dut.write_valid.value = 0
    dut.read_valid.value = 0
    dut.write_addr.value = 0
    dut.read_addr.value = 0
    dut.write_data.value = 0
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    async def tick():
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

    await tick()
    dut.rst_n.value = 1

    async def cycle(swap=0, wvalid=0, rvalid=0, wa=0, ra=0, wd=0):
        nonlocal active, writes, reads, swaps
        dut.swap.value = swap
        dut.write_valid.value = wvalid
        dut.read_valid.value = rvalid
        dut.write_addr.value = wa
        dut.read_addr.value = ra
        dut.write_data.value = wd
        await Timer(1, units="ns")
        can_swap = not (wvalid or rvalid)
        assert int(dut.swap_ready.value) == int(can_swap)
        if rvalid and not swap and model[active][ra] is not None:
            assert int(dut.read_data.value) == model[active][ra]
        await tick()
        if swap and can_swap:
            active ^= 1
            swaps += 1
        if wvalid and not swap:
            model[1-active][wa] = wd
            writes += 1
        if rvalid and not swap:
            reads += 1
        assert int(dut.active_bank.value) == active
        assert int(dut.write_count.value) == writes
        assert int(dut.read_count.value) == reads
        assert int(dut.swap_count.value) == swaps

    # Preload inactive bank 1 then make it active.
    for addr in range(depth):
        await cycle(wvalid=1, wa=addr, wd=(addr*7+3) & 255)
    await cycle(swap=1)
    # Consume bank 1 while loading bank 0, both in the same clock.
    for addr in range(depth):
        await cycle(wvalid=1, rvalid=1, wa=addr, ra=addr,
                    wd=(addr*13+5) & 255)
    # Swap cannot interrupt outstanding traffic.
    await cycle(swap=1, wvalid=1, rvalid=1, wa=0, ra=0)
    await cycle(swap=1)
    # Consume bank 0 and refill bank 1 under random concurrent traffic.
    for _ in range(400):
        wa, ra = rng.randrange(depth), rng.randrange(depth)
        await cycle(wvalid=1, rvalid=1, wa=wa, ra=ra,
                    wd=rng.randrange(256))
    await cycle(swap=1)
    for addr in range(depth):
        await cycle(rvalid=1, ra=addr)

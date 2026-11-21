import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def host_programs_and_reads_matrix(dut):
    dut.rst_n.value = 0
    dut.req_valid.value = 0
    dut.req_write.value = 0
    dut.req_addr.value = 0
    dut.req_wdata.value = 0
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    async def tick():
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

    async def write(addr, data):
        dut.req_addr.value = addr
        dut.req_wdata.value = data
        dut.req_valid.value = 1
        dut.req_write.value = 1
        await tick()
        dut.req_valid.value = 0
        dut.req_write.value = 0

    async def read(addr):
        dut.req_addr.value = addr
        dut.req_valid.value = 1
        dut.req_write.value = 0
        await Timer(1, units="ns")
        value = int(dut.req_rdata.value)
        dut.req_valid.value = 0
        return value

    await tick()
    dut.rst_n.value = 1
    await write(0x00, 2)  # IRQ enabled
    await write(0x08, 3 << 8)  # INT8 K=3
    assert await read(0x08) == (3 << 8)
    a = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]
    b = [[2, 1, 0, 3], [1, 0, 2, 4], [3, 2, 1, 5]]
    for r in range(4):
        for k in range(3):
            await write(0x20, r*32+k)
            await write(0x24, a[r][k])
    for k in range(3):
        for c in range(4):
            await write(0x28, k*4+c)
            await write(0x2c, b[k][c])
    await write(0x00, 3)  # START and keep IRQ enabled
    assert (await read(0x04)) & 1
    for _ in range(25):
        await tick()
        if (await read(0x04)) & 2:
            break
    else:
        assert False, "tile did not complete"
    await tick()  # IRQ pending is registered after done
    assert int(dut.irq.value) == 1
    assert await read(0x0c) == 3 + 2*4 - 1
    for r in range(4):
        for c in range(4):
            await write(0x18, r*4+c)
            actual = await read(0x1c)
            expected = sum(a[r][k]*b[k][c] for k in range(3))
            assert actual == expected, (r, c, actual, expected)
    await write(0x14, 1)
    assert int(dut.irq.value) == 0

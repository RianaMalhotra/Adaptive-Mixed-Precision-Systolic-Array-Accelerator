import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def loads_partial_tiles_with_padding(dut):
    n, kt = 4, 32
    m,k,p = 5,33,6
    a = [(r*7+t*3)&255 for r in range(m) for t in range(k)]
    b = [(t*5+c*11)&255 for t in range(k) for c in range(p)]
    dut.rst_n.value = 0
    dut.start.value = 0
    dut.m_dim.value = m
    dut.k_dim.value = k
    dut.p_dim.value = p
    dut.tile_row.value = 1
    dut.tile_col.value = 1
    dut.k_block.value = 1
    dut.current_k_len.value = 1
    dut.a_read_data.value = 0
    dut.b_read_data.value = 0
    cocotb.start_soon(Clock(dut.clk,10,units="ns").start())

    async def tick():
        await RisingEdge(dut.clk)
        await Timer(1,units="ns")

    await tick()
    dut.rst_n.value = 1
    dut.start.value = 1
    await tick()
    dut.start.value = 0
    aw, bw = {}, {}
    for _ in range(2*n*kt):
        assert int(dut.busy.value) == 1
        ar = int(dut.a_read.value)
        br = int(dut.b_read.value)
        ai = int(dut.a_read_addr.value)
        bi = int(dut.b_read_addr.value)
        dut.a_read_data.value = a[ai] if ar else 0
        dut.b_read_data.value = b[bi] if br else 0
        await Timer(1,units="ns")
        addr = int(dut.write_addr.value)
        data = int(dut.write_data.value)
        if int(dut.a_write.value):
            aw[addr] = data
        if int(dut.b_write.value):
            bw[addr] = data
        await tick()
    assert int(dut.done.value) == 1
    assert int(dut.busy.value) == 0
    assert len(aw) == len(bw) == n*kt
    for r in range(n):
        for t in range(kt):
            expected = a[(r+4)*k+32+t] if r==0 and t==0 else 0
            assert aw[r*kt+t] == expected
    for t in range(kt):
        for c in range(n):
            expected = b[32*p+4+c] if t==0 and c<2 else 0
            assert bw[t*n+c] == expected

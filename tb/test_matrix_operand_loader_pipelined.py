import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def synchronous_sram_read_latency_and_padding(dut):
    m,k,p = 5,33,6
    a = [(r*7+t*3)&255 for r in range(m) for t in range(k)]
    b = [(t*5+c*11)&255 for t in range(k) for c in range(p)]
    dut.rst_n.value=0
    dut.start.value=0
    dut.m_dim.value=m
    dut.k_dim.value=k
    dut.p_dim.value=p
    dut.tile_row.value=1
    dut.tile_col.value=1
    dut.k_block.value=1
    dut.current_k_len.value=1
    dut.a_read_data.value=0
    dut.b_read_data.value=0
    cocotb.start_soon(Clock(dut.clk,10,units="ns").start())
    async def tick():
        # Registered SRAM outputs update after the edge that samples read-enable.
        ar=int(dut.a_read.value)
        br=int(dut.b_read.value)
        ai=int(dut.a_read_addr.value)
        bi=int(dut.b_read_addr.value)
        await RisingEdge(dut.clk)
        if ar: dut.a_read_data.value=a[ai]
        if br: dut.b_read_data.value=b[bi]
        await Timer(1,units="ns")
    await tick()
    dut.rst_n.value=1
    dut.start.value=1
    await tick()
    dut.start.value=0
    aw,bw={},{}
    for elapsed in range(258):
        if int(dut.a_write.value): aw[int(dut.write_addr.value)]=int(dut.write_data.value)
        if int(dut.b_write.value): bw[int(dut.write_addr.value)]=int(dut.write_data.value)
        if int(dut.done.value): break
        await tick()
    assert int(dut.done.value)==1
    assert elapsed == 257, elapsed
    assert len(aw)==len(bw)==128
    for r in range(4):
        for t in range(32):
            expected=a[4*k+32] if r==0 and t==0 else 0
            assert aw[r*32+t]==expected
    for t in range(32):
        for c in range(4):
            expected=b[32*p+4+c] if t==0 and c<2 else 0
            assert bw[t*4+c]==expected

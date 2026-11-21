import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def full_matrix_partial_tiles_and_reduction(dut):
    # M=5, K=33, P=5: 2x2 output tiles, two reduction blocks each.
    m,k,p = 5,33,5
    a = [[((r*3+t)%11)-5 for t in range(k)] for r in range(m)]
    b = [[((t*2+c)%9)-4 for c in range(p)] for t in range(k)]
    dut.rst_n.value = 0
    dut.start.value = 0
    dut.operands_ready.value = 0
    dut.enable.value = 1
    dut.mode_int4.value = 0
    dut.m_dim.value = m
    dut.k_dim.value = k
    dut.p_dim.value = p
    dut.a_write.value = 0
    dut.b_write.value = 0
    dut.write_addr.value = 0
    dut.write_data.value = 0
    dut.read_row.value = 0
    dut.read_col.value = 0
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    async def tick():
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

    async def write(is_a,addr,data):
        dut.a_write.value = int(is_a)
        dut.b_write.value = int(not is_a)
        dut.write_addr.value = addr
        dut.write_data.value = data & 255
        await tick()

    await tick()
    dut.rst_n.value = 1
    dut.start.value = 1
    await tick()
    dut.start.value = 0
    for i in range(8):
        for _ in range(5):
            if int(dut.waiting_for_operands.value):
                break
            await tick()
        assert int(dut.waiting_for_operands.value)
        tr,tc,kb = [int(getattr(dut,x).value) for x in ("tile_row","tile_col","k_block")]
        length = int(dut.current_k_len.value)
        assert (tr,tc,kb) == ((i//2)//2,(i//2)%2,i%2)
        for r in range(4):
            for t in range(length):
                gr,gk = tr*4+r,kb*32+t
                await write(True,r*32+t,a[gr][gk] if gr<m else 0)
        for t in range(length):
            for c in range(4):
                gk,gc = kb*32+t,tc*4+c
                await write(False,t*4+c,b[gk][gc] if gc<p else 0)
        dut.a_write.value = 0
        dut.b_write.value = 0
        dut.operands_ready.value = 1
        await tick()
        dut.operands_ready.value = 0
        for _ in range(100):
            await tick()
            if int(dut.tiles_visited.value) == i+1:
                break
        else:
            assert False, "tile timeout"
    assert int(dut.job_done.value) == 1
    assert int(dut.accepted_writes.value) == 2*m*p
    for r in range(m):
        for c in range(p):
            dut.read_row.value = r
            dut.read_col.value = c
            await Timer(1,units="ns")
            expected = sum(a[r][t]*b[t][c] for t in range(k))
            got = int(dut.read_data.value)
            if got >= 2**31:
                got -= 2**32
            assert int(dut.read_valid.value) == 1
            assert got == expected,(r,c,got,expected)

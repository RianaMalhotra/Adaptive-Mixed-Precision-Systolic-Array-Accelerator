import random
import cocotb
from cocotb.triggers import Timer


@cocotb.test()
async def address_and_boundary_regression(dut):
    rng = random.Random(7124)
    cases = [(1,1,1),(4,32,4),(5,33,7),(9,65,11),(3,1,6)]
    cases += [(rng.randint(1,50),rng.randint(1,90),rng.randint(1,50))
              for _ in range(50)]
    for m,k,p in cases:
        dut.m_dim.value = m
        dut.k_dim.value = k
        dut.p_dim.value = p
        for tr in range((m+3)//4):
            for tc in range((p+3)//4):
                for kb in range((k+31)//32):
                    for _ in range(5):
                        r = rng.randrange(4)
                        c = rng.randrange(4)
                        t = rng.randrange(32)
                        dut.tile_row.value = tr
                        dut.tile_col.value = tc
                        dut.k_block.value = kb
                        dut.row_lane.value = r
                        dut.col_lane.value = c
                        dut.reduction_lane.value = t
                        await Timer(1, units="ns")
                        gr, gc, gk = tr*4+r, tc*4+c, kb*32+t
                        assert int(dut.a_offset.value) == gr*k+gk
                        assert int(dut.b_offset.value) == gk*p+gc
                        assert int(dut.c_offset.value) == gr*p+gc
                        assert int(dut.a_valid.value) == int(gr<m and gk<k)
                        assert int(dut.b_valid.value) == int(gk<k and gc<p)
                        assert int(dut.c_valid.value) == int(gr<m and gc<p)

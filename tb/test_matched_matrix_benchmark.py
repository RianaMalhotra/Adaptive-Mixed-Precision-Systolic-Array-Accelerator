"""Matched cycle benchmarks for sequential and overlapped SRAM staging."""
import csv
import os
import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def matched_matrix_benchmark(dut):
    rng = random.Random(2026)
    variant = os.environ.get("TENSORFORGE_VARIANT", "unknown")
    rows = []
    dut.start.value = 0
    dut.rst_n.value = 0
    dut.enable.value = 1
    dut.a_read_data.value = 0
    dut.b_read_data.value = 0
    dut.read_row.value = 0
    dut.read_col.value = 0
    dut.m_dim.value = 0
    dut.k_dim.value = 0
    dut.p_dim.value = 0
    dut.mode_int4.value = 0
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    a, b = [], []

    async def tick():
        await Timer(1, units="ns")
        ar, br = int(dut.a_read.value), int(dut.b_read.value)
        ai, bi = int(dut.a_read_addr.value), int(dut.b_read_addr.value)
        await RisingEdge(dut.clk)
        if ar:
            dut.a_read_data.value = a[ai]
        if br:
            dut.b_read_data.value = b[bi]
        await Timer(1, units="ns")

    def signed(v, bits):
        return v - (1 << bits) if v & (1 << (bits-1)) else v

    await tick()
    for mode in (0, 1):
        for m,k,p in [(4,32,4),(5,33,5),(8,64,8),(7,65,6)]:
            dut.rst_n.value = 0
            await tick()
            a = [rng.randrange(256) for _ in range(m*k)]
            b = [rng.randrange(256) for _ in range(k*p)]
            dut.m_dim.value, dut.k_dim.value, dut.p_dim.value = m,k,p
            dut.mode_int4.value = mode
            dut.rst_n.value = 1
            dut.start.value = 1
            await tick()
            dut.start.value = 0
            load = compute = wb = overlap = 0
            for cycles in range(1, 30001):
                l,e,w = (int(dut.loader_busy.value), int(dut.engine_busy.value),
                         int(dut.writeback_busy.value))
                load += l
                compute += e
                wb += w
                overlap += l & e
                await tick()
                if int(dut.job_done.value):
                    break
            else:
                assert False, "benchmark timeout"
            for row in range(m):
                for col in range(p):
                    dut.read_row.value, dut.read_col.value = row,col
                    await Timer(1, units="ns")
                    expected = 0
                    for t in range(k):
                        av,bv = a[row*k+t],b[t*p+col]
                        if mode:
                            expected += signed(av&15,4)*signed(bv&15,4)
                            expected += signed(av>>4,4)*signed(bv>>4,4)
                        else:
                            expected += signed(av,8)*signed(bv,8)
                    assert int(dut.read_valid.value)
                    assert signed(int(dut.read_data.value),32) == expected
            macs = m*k*p*(1+mode)
            result = dict(variant=variant,precision="INT4" if mode else "INT8",
                          m=m,k=k,p=p,cycles=cycles,loader_cycles=load,
                          compute_cycles=compute,writeback_cycles=wb,
                          overlap_cycles=overlap,useful_macs=macs,
                          macs_per_cycle=macs/cycles)
            rows.append(result)
            dut._log.info("BENCH %s", result)
    path = os.environ.get("TENSORFORGE_MATRIX_CSV")
    if path:
        with open(path,"w",newline="") as f:
            writer = csv.DictWriter(f,fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

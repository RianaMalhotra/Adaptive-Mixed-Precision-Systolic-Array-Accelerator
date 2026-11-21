"""Cycle-accurate performance regression for the programmable tile engine."""
import csv
import os
import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def benchmark_tile_latency_and_stalls(dut):
    rng = random.Random(4107)
    n, kmax = 4, 32
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

    async def write(a_bank, address, data):
        dut.a_write.value = int(a_bank)
        dut.b_write.value = int(not a_bank)
        dut.write_addr.value = address
        dut.write_data.value = data
        await tick()

    await tick()
    dut.rst_n.value = 1
    records = []
    for packed in (0, 1):
        for k in (1, 4, 8, 16, 32):
            for stall_period in (0, 5):
                a = [[rng.randrange(256) for _ in range(k)] for _ in range(n)]
                b = [[rng.randrange(256) for _ in range(n)] for _ in range(k)]
                for r in range(n):
                    for t in range(k):
                        await write(True, r*kmax+t, a[r][t])
                for t in range(k):
                    for c in range(n):
                        await write(False, t*n+c, b[t][c])
                dut.a_write.value = 0
                dut.b_write.value = 0
                dut.mode_int4.value = packed
                dut.k_len.value = k
                dut.start.value = 1
                dut.enable.value = 1
                await tick()
                dut.start.value = 0
                wall = 0
                stalls = 0
                while int(dut.busy.value):
                    disabled = bool(stall_period and wall % stall_period == stall_period-1)
                    dut.enable.value = int(not disabled)
                    await tick()
                    wall += 1
                    stalls += int(disabled)
                    assert wall <= 2*(k+2*n+1), "controller exceeded timeout"
                expected_compute = k+2*n-1
                assert int(dut.done.value) == 1
                assert int(dut.cycle_count.value) == expected_compute
                assert int(dut.stall_count.value) == stalls
                assert wall == expected_compute + stalls
                # MAC work per tile: N*N*K; packed INT4 performs 2 multiplies per PE.
                macs = n*n*k*(2 if packed else 1)
                ideal_peak = n*n*(2 if packed else 1)
                utilization = macs/(wall*ideal_peak)
                records.append((packed, k, stall_period, expected_compute, stalls,
                                wall, macs, round(utilization, 6)))
    path = os.getenv("TENSORFORGE_BENCH_CSV")
    if path:
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(("int4", "k", "stall_period", "compute_cycles",
                             "stall_cycles", "elapsed_cycles", "scalar_macs",
                             "effective_array_utilization"))
            writer.writerows(records)
    assert len(records) == 20

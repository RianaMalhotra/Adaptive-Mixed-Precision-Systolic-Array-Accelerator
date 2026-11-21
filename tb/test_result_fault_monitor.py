import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def fault_injection_and_sticky_diagnostics(dut):
    rng = random.Random(6626)
    dut.rst_n.value = 0
    dut.clear_status.value = 0
    dut.sample_valid.value = 0
    dut.sample_index.value = 0
    dut.reference_result.value = 0
    dut.inject_enable.value = 0
    dut.inject_mask.value = 0
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    async def tick():
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

    await tick()
    dut.rst_n.value = 1
    samples = faults = 0
    sticky = 0
    first = 0
    for cycle in range(500):
        data = rng.getrandbits(32)
        mask = (1 << rng.randrange(32)) if cycle % 7 == 0 else rng.getrandbits(32)
        inject = int(cycle % 5 == 0)
        valid = int(cycle % 9 != 0)
        index = cycle % 16
        clear = int(cycle in (170, 340))
        dut.reference_result.value = data
        dut.inject_mask.value = mask
        dut.inject_enable.value = inject
        dut.sample_valid.value = valid
        dut.sample_index.value = index
        dut.clear_status.value = clear
        await Timer(1, units="ns")
        observed = data ^ (mask if inject else 0)
        mismatch = bool(valid and observed != data)
        assert int(dut.observed_result.value) == observed
        assert int(dut.mismatch.value) == int(mismatch)
        await tick()
        if clear:
            samples = faults = sticky = first = 0
        elif valid:
            samples += 1
            if mismatch:
                faults += 1
                if not sticky:
                    first = index
                sticky = 1
        assert int(dut.sample_count.value) == samples
        assert int(dut.fault_count.value) == faults
        assert int(dut.fault_sticky.value) == sticky
        assert int(dut.first_fault_index.value) == first
    # Fault mask zero must not flag an error.
    dut.clear_status.value = 1
    await tick()
    dut.clear_status.value = 0
    dut.sample_valid.value = 1
    dut.inject_enable.value = 1
    dut.inject_mask.value = 0
    await Timer(1, units="ns")
    assert int(dut.mismatch.value) == 0
    await tick()
    assert int(dut.fault_count.value) == 0

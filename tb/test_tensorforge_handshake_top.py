import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def delayed_memory_and_compute_stalls(dut):
    rng = random.Random(2718)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    for name in ("start","rst_n","enable","a_req_ready","b_req_ready",
                 "a_rsp_valid","b_rsp_valid","a_read_data","b_read_data",
                 "read_row","read_col","m_dim","k_dim","p_dim","mode_int4"):
        getattr(dut,name).value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")

    def signed(v,bits):
        return v-(1<<bits) if v & (1<<(bits-1)) else v

    for m,k,p,mode in [(1,1,1,0),(5,33,5,0),(3,31,5,1),(5,65,3,1)]:
        a = [rng.randrange(256) for _ in range(m*k)]
        b = [rng.randrange(256) for _ in range(k*p)]
        dut.rst_n.value = 0
        dut.a_rsp_valid.value = dut.b_rsp_valid.value = 0
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        dut.m_dim.value,dut.k_dim.value,dut.p_dim.value = m,k,p
        dut.mode_int4.value = mode
        dut.rst_n.value = 1
        dut.start.value = 1
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        dut.start.value = 0
        pending = {}
        held = {}
        requests = responses = blocked = 0
        for cycle in range(50000):
            dut.enable.value = int(rng.random() > .25)
            for port in ("a","b"):
                getattr(dut,port+"_req_ready").value = int(rng.random() > .4)
                entry = pending.get(port)
                valid = entry is not None and cycle >= entry[0]
                getattr(dut,port+"_rsp_valid").value = int(valid)
                if valid:
                    getattr(dut,port+"_read_data").value = entry[1]
            await Timer(1, units="ns")
            for port,mem in (("a",a),("b",b)):
                req = int(getattr(dut,port+"_read").value)
                addr = int(getattr(dut,port+"_read_addr").value)
                ready = int(getattr(dut,port+"_req_ready").value)
                if port in held:
                    assert req and addr == held[port], "request changed under backpressure"
                if req and not ready:
                    held[port] = addr
                    blocked += 1
                else:
                    held.pop(port,None)
                if req and ready:
                    assert not pending, "more than one outstanding request"
                    assert addr < len(mem)
                    pending[port] = (cycle+rng.randint(1,8),mem[addr])
                    requests += 1
                if int(getattr(dut,port+"_rsp_valid").value) and int(getattr(dut,port+"_rsp_ready").value):
                    del pending[port]
                    responses += 1
            await RisingEdge(dut.clk)
            await Timer(1, units="ns")
            if int(dut.job_done.value):
                break
        else:
            assert False, "handshake job timed out"
        assert not pending and requests == responses
        assert requests == m*k*((p+3)//4)+k*p*((m+3)//4)
        if m*k*p > 1:
            assert blocked > 0
        for row in range(m):
            for col in range(p):
                dut.read_row.value,dut.read_col.value = row,col
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

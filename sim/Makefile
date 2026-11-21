SIM ?= verilator
TOPLEVEL_LANG = verilog
export PYTHONPATH := $(abspath ../tb):$(PYTHONPATH)
VERILOG_SOURCES = $(abspath ../rtl/compute/mixed_precision_pe.sv)
TOPLEVEL = mixed_precision_pe
MODULE = test_mixed_precision_pe
include $(shell cocotb-config --makefiles)/Makefile.sim

.PHONY: array tile buffer regs dfx
array:
	$(MAKE) SIM=$(SIM) TOPLEVEL=systolic_array MODULE=test_systolic_array VERILOG_SOURCES="$(abspath ../rtl/compute/mixed_precision_pe.sv) $(abspath ../rtl/compute/systolic_array.sv)" SIM_BUILD=sim_build_array
tile:
	$(MAKE) SIM=$(SIM) TOPLEVEL=tile_engine MODULE=test_tile_engine VERILOG_SOURCES="$(abspath ../rtl/compute/mixed_precision_pe.sv) $(abspath ../rtl/compute/systolic_array.sv) $(abspath ../rtl/control/tile_engine.sv)" SIM_BUILD=sim_build_tile
buffer:
	$(MAKE) SIM=$(SIM) TOPLEVEL=ping_pong_buffer MODULE=test_ping_pong_buffer VERILOG_SOURCES="$(abspath ../rtl/memory/ping_pong_buffer.sv)" SIM_BUILD=sim_build_buffer
regs:
	$(MAKE) SIM=$(SIM) TOPLEVEL=accelerator_regs MODULE=test_accelerator_regs VERILOG_SOURCES="$(abspath ../rtl/compute/mixed_precision_pe.sv) $(abspath ../rtl/compute/systolic_array.sv) $(abspath ../rtl/control/tile_engine.sv) $(abspath ../rtl/dft/result_fault_monitor.sv) $(abspath ../rtl/control/accelerator_regs.sv)" SIM_BUILD=sim_build_regs
dfx:
	$(MAKE) SIM=$(SIM) TOPLEVEL=result_fault_monitor MODULE=test_result_fault_monitor VERILOG_SOURCES="$(abspath ../rtl/dft/result_fault_monitor.sv)" SIM_BUILD=sim_build_dfx

.PHONY: benchmark
benchmark:
	$(MAKE) SIM=$(SIM) TOPLEVEL=tile_engine MODULE=test_tile_performance VERILOG_SOURCES="$(abspath ../rtl/compute/mixed_precision_pe.sv) $(abspath ../rtl/compute/systolic_array.sv) $(abspath ../rtl/control/tile_engine.sv)" SIM_BUILD=sim_build_benchmark

.PHONY: double_buffered
double_buffered:
	$(MAKE) SIM=$(SIM) TOPLEVEL=double_buffered_tile_engine MODULE=test_double_buffered_tile_engine VERILOG_SOURCES="$(abspath ../rtl/compute/mixed_precision_pe.sv) $(abspath ../rtl/compute/systolic_array.sv) $(abspath ../rtl/control/double_buffered_tile_engine.sv)" SIM_BUILD=sim_build_double_buffered

.PHONY: scheduler
scheduler:
	$(MAKE) SIM=$(SIM) TOPLEVEL=multi_tile_scheduler MODULE=test_multi_tile_scheduler VERILOG_SOURCES="$(abspath ../rtl/control/multi_tile_scheduler.sv)" SIM_BUILD=sim_build_scheduler

.PHONY: multitile
multitile:
	$(MAKE) SIM=$(SIM) TOPLEVEL=tensorforge_multitile_top MODULE=test_tensorforge_multitile_top VERILOG_SOURCES="$(abspath ../rtl/compute/mixed_precision_pe.sv) $(abspath ../rtl/compute/systolic_array.sv) $(abspath ../rtl/control/double_buffered_tile_engine.sv) $(abspath ../rtl/control/multi_tile_scheduler.sv) $(abspath ../rtl/top/tensorforge_multitile_top.sv)" SIM_BUILD=sim_build_multitile

SIM ?= verilator
TOPLEVEL_LANG = verilog
export PYTHONPATH := $(abspath ../tb):$(PYTHONPATH)
VERILOG_SOURCES = $(abspath ../rtl/compute/mixed_precision_pe.sv)
TOPLEVEL = mixed_precision_pe
MODULE = test_mixed_precision_pe
include $(shell cocotb-config --makefiles)/Makefile.sim

.PHONY: array tile
array:
	$(MAKE) SIM=$(SIM) TOPLEVEL=systolic_array MODULE=test_systolic_array VERILOG_SOURCES="$(abspath ../rtl/compute/mixed_precision_pe.sv) $(abspath ../rtl/compute/systolic_array.sv)" SIM_BUILD=sim_build_array
tile:
	$(MAKE) SIM=$(SIM) TOPLEVEL=tile_engine MODULE=test_tile_engine VERILOG_SOURCES="$(abspath ../rtl/compute/mixed_precision_pe.sv) $(abspath ../rtl/compute/systolic_array.sv) $(abspath ../rtl/control/tile_engine.sv)" SIM_BUILD=sim_build_tile

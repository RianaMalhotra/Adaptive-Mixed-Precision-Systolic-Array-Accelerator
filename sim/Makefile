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
	$(MAKE) SIM=$(SIM) TOPLEVEL=tensorforge_multitile_top MODULE=test_tensorforge_multitile_top VERILOG_SOURCES="$(abspath ../rtl/compute/mixed_precision_pe.sv) $(abspath ../rtl/compute/systolic_array.sv) $(abspath ../rtl/control/double_buffered_tile_engine.sv) $(abspath ../rtl/control/multi_tile_scheduler.sv) $(abspath ../rtl/control/tile_writeback_sequencer.sv) $(abspath ../rtl/memory/output_accumulator.sv) $(abspath ../rtl/top/tensorforge_multitile_top.sv)" SIM_BUILD=sim_build_multitile

.PHONY: addressing
addressing:
	$(MAKE) SIM=$(SIM) TOPLEVEL=matrix_tile_address_gen MODULE=test_matrix_tile_address_gen VERILOG_SOURCES="$(abspath ../rtl/control/matrix_tile_address_gen.sv)" SIM_BUILD=sim_build_addressing

.PHONY: writeback
writeback:
	$(MAKE) SIM=$(SIM) TOPLEVEL=output_accumulator MODULE=test_output_accumulator VERILOG_SOURCES="$(abspath ../rtl/memory/output_accumulator.sv)" SIM_BUILD=sim_build_writeback

.PHONY: writeback_sequencer
writeback_sequencer:
	$(MAKE) SIM=$(SIM) TOPLEVEL=tile_writeback_sequencer MODULE=test_tile_writeback_sequencer VERILOG_SOURCES="$(abspath ../rtl/control/tile_writeback_sequencer.sv)" SIM_BUILD=sim_build_writeback_sequencer

.PHONY: iterator
iterator:
	$(MAKE) SIM=$(SIM) TOPLEVEL=matrix_tile_iterator MODULE=test_matrix_tile_iterator VERILOG_SOURCES="$(abspath ../rtl/control/matrix_tile_iterator.sv)" SIM_BUILD=sim_build_iterator

.PHONY: matrix_job
matrix_job:
	$(MAKE) SIM=$(SIM) TOPLEVEL=matrix_job_controller MODULE=test_matrix_job_controller VERILOG_SOURCES="$(abspath ../rtl/control/matrix_tile_iterator.sv) $(abspath ../rtl/control/matrix_job_controller.sv)" SIM_BUILD=sim_build_matrix_job

.PHONY: matrix_integration
matrix_integration:
	$(MAKE) SIM=$(SIM) TOPLEVEL=tensorforge_matrix_job_top MODULE=test_tensorforge_matrix_job_top VERILOG_SOURCES="$(abspath ../rtl/compute/mixed_precision_pe.sv) $(abspath ../rtl/compute/systolic_array.sv) $(abspath ../rtl/control/double_buffered_tile_engine.sv) $(abspath ../rtl/control/matrix_tile_iterator.sv) $(abspath ../rtl/control/matrix_job_controller.sv) $(abspath ../rtl/control/tile_writeback_sequencer.sv) $(abspath ../rtl/memory/output_accumulator.sv) $(abspath ../rtl/top/tensorforge_matrix_job_top.sv)" SIM_BUILD=sim_build_matrix_integration

.PHONY: operand_loader
operand_loader:
	$(MAKE) SIM=$(SIM) TOPLEVEL=matrix_operand_loader MODULE=test_matrix_operand_loader VERILOG_SOURCES="$(abspath ../rtl/control/matrix_operand_loader.sv)" SIM_BUILD=sim_build_operand_loader

.PHONY: autoload
autoload:
	$(MAKE) SIM=$(SIM) TOPLEVEL=tensorforge_autoload_top MODULE=test_tensorforge_autoload_top VERILOG_SOURCES="$(abspath ../rtl/compute/mixed_precision_pe.sv) $(abspath ../rtl/compute/systolic_array.sv) $(abspath ../rtl/control/double_buffered_tile_engine.sv) $(abspath ../rtl/control/matrix_tile_iterator.sv) $(abspath ../rtl/control/matrix_job_controller.sv) $(abspath ../rtl/control/matrix_operand_loader.sv) $(abspath ../rtl/control/tile_writeback_sequencer.sv) $(abspath ../rtl/memory/output_accumulator.sv) $(abspath ../rtl/top/tensorforge_matrix_job_top.sv) $(abspath ../rtl/top/tensorforge_autoload_top.sv)" SIM_BUILD=sim_build_autoload

.PHONY: operand_loader_sync
operand_loader_sync:
	$(MAKE) SIM=$(SIM) TOPLEVEL=matrix_operand_loader_sync MODULE=test_matrix_operand_loader_sync VERILOG_SOURCES="$(abspath ../rtl/control/matrix_operand_loader_sync.sv)" SIM_BUILD=sim_build_operand_loader_sync

.PHONY: sync_autoload
sync_autoload:
	$(MAKE) SIM=$(SIM) TOPLEVEL=tensorforge_sync_autoload_top MODULE=test_tensorforge_sync_autoload_top VERILOG_SOURCES="$(abspath ../rtl/compute/mixed_precision_pe.sv) $(abspath ../rtl/compute/systolic_array.sv) $(abspath ../rtl/control/double_buffered_tile_engine.sv) $(abspath ../rtl/control/matrix_tile_iterator.sv) $(abspath ../rtl/control/matrix_job_controller.sv) $(abspath ../rtl/control/matrix_operand_loader_sync.sv) $(abspath ../rtl/control/tile_writeback_sequencer.sv) $(abspath ../rtl/memory/output_accumulator.sv) $(abspath ../rtl/top/tensorforge_matrix_job_top.sv) $(abspath ../rtl/top/tensorforge_sync_autoload_top.sv)" SIM_BUILD=sim_build_sync_autoload

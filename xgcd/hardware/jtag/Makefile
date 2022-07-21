#!/bin/bash

#######################
# Parameters
#######################
TOP_MODULE = jtag_wrapper
GENESIS_DIR = ./genesis
GENESIS_FILES := $(wildcard $(GENESIS_DIR)/*.svp)
RTL_OUTPUT_DIR = rtl
TB_RTL_DIR = tb_rtl

XRUN = xrun \
       -64bit \
       -sv \
       -sysv \
       -l xrun.log \
       -notimingchecks \
       -covoverwrite \
       -top top \
       -timescale 100ps/1ps \
       +loadpli1=debpli:deb_PLIPtr \
       -initmem0 \
       -initreg0 \
       +access+rwc \
       +maxdelays \
       -vcdextend \
       -input "sim/cmd.tcl" \
       -y ${DW_ALL_PATH} \
       -incdir ${DW_ALL_PATH} \
       +libext+.v+.sv+.inc \
       $(XRUNARGS) \
       $(DESIGNARGS)

#######################
# genesis
#######################
.PHONY: rtl
rtl: $(GENESIS_FILES)
	rm -rf $(RTL_OUTPUT_DIR)
	Genesis2.pl -parse -generate -top ${TOP_MODULE} -inputlist $(GENESIS_DIR)/$(TOP_MODULE).genesis.filelist
	mv genesis_verif $(RTL_OUTPUT_DIR)
	find $(RTL_OUTPUT_DIR) -type f -name '*.sv' | xargs realpath  > $(TOP_MODULE).filelist
	echo ${DW_ALL_PATH}"/DW_tap.v" >> $(TOP_MODULE).filelist

#######################
# sim
#######################
sim_genesis:
	rm -rf $(TB_RTL_DIR)
	Genesis2.pl -parse -generate -top top -inputlist sim/tb_$(TOP_MODULE).genesis.filelist $(GENESIS_DIR)/$(TOP_MODULE).genesis.filelist
	mv genesis_verif $(TB_RTL_DIR)

sim: DESIGNARGS += \
    -F tb_$(TOP_MODULE).filelist
sim: sim_genesis 
	$(XRUN)

#######################
# clean
#######################
.PHONY: clean
clean:
	rm -rf coverage.vdb csrc DVEfiles inter.vpd simv simv.daidir ucli.key vc_hdrs.h vcs.log INCA_libs xrun.history xrun.log $(TOP_MODULE).filelist


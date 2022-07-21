#=========================================================================
# main.tcl
#=========================================================================
# Run the foundation flow step
#
# Author : Christopher Torng
# Date   : January 13, 2020

source -verbose innovus-foundation-flow/INNOVUS/run_init.tcl

setDontUse sky130_fd_sc_hd__probec_p_8 true 
setDontUse sky130_fd_sc_hd__probe_p_8 true 
setDontUse sky130_fd_sc_hd__tt_025C_1v80/sky130_fd_sc_hd__probec_p_8 true
setDontUse sky130_fd_sc_hd__tt_025C_1v80/sky130_fd_sc_hd__probe_p_8 true

setDontUse sky130_fd_sc_hd__xor3_4 true
setDontUse sky130_fd_sc_hd__tt_025C_1v80/sky130_fd_sc_hd__xor3_4 true

setDontUse [get_lib_cells sky130_fd_sc_hd__tt_025C_1v80/sky130_fd_sc_hd__probe_p_*] true
setDontUse [get_lib_cells sky130_fd_sc_hd__probe_p_*] true
setDontUse [get_lib_cells {*/*probec* }] true

setDontUse sky130_fd_sc_hd__tt_025C_1v80/sky130_fd_sc_hd__probe_p_c true
setDontUse sky130_fd_sc_hd__probe_p_c true
setDontUse sky130_fd_sc_hd__tt_025C_1v80/sky130_fd_sc_hd__probe_pc True
setDontUse sky130_fd_sc_hd__probe_pc true
setDontUse sky130_fd_sc_hd__tt_025C_1v80/sky130_fd_sc_hd__probe_p_* True
setDontUse sky130_fd_sc_hd__probe_p_* true

setDontUse */*probec* true

setDontUse sky130_fd_sc_hd__tt_025C_1v80/sky130_fd_sc_hd__xor3_4
setDontUse sky130_fd_sc_hd__xor3_4

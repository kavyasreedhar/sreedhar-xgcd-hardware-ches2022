#=========================================================================
# Design Constraints File
#=========================================================================

# This constraint sets the target clock period for the chip in
# nanoseconds. Note that the first parameter is the name of the clock
# signal in your verlog design. If you called it something different than
# clk you will need to change this. You should set this constraint
# carefully. If the period is unrealistically small then the tools will
# spend forever trying to meet timing and ultimately fail. If the period
# is too large the tools will have no trouble but you will get a very
# conservative implementation.

set clock_net  clk 
set clock_name ideal_clock

create_clock -name ${clock_name} \
             -period ${dc_clock_period} \
             [get_ports ${clock_net}]

# JTAG nets

set jtag_net  io_in[29]
set jtag_name jtag_clock

create_clock -name ${jtag_name} \
             -period [expr 20 * ${dc_clock_period}] \
             [get_ports ${jtag_net}]

# Clock groups -- Set the system clock and jtag clock to be async (this
# sets false paths between all flops in each domain)

set_clock_groups -asynchronous \
                 -group $clock_name \
                 -group $jtag_name

# This constraint sets the load capacitance in picofarads of the
# output pins of your design.

set_load -pin_load $ADK_TYPICAL_ON_CHIP_LOAD [all_outputs]

# This constraint sets the input drive strength of the input pins of
# your design. We specify a specific standard cell which models what
# would be driving the inputs. This should usually be a small inverter
# which is reasonable if another block of on-chip logic is driving
# your inputs.

set_driving_cell -no_design_rule \
  -lib_cell $ADK_DRIVING_CELL [all_inputs]

# set_input_delay constraints for input ports
set_input_delay -clock ${clock_name} 0 [all_inputs]
# set_output_delay constraints for output ports
set_output_delay -clock ${clock_name} 0 [all_outputs]

# Make all signals limit their fanout

set_max_fanout 20 $dc_design_name

# Make all signals meet good slew

set_max_transition [expr 0.25*${dc_clock_period}] $dc_design_name

set_dont_use [get_lib_cells sky130_fd_sc_hd__tt_025C_1v80/sky130_fd_sc_hd__xor3_4]
set_dont_use [get_lib_cells {*/*probec* }]

set PART xc7k410tfbg676-1;
set SRC inputs/design.v;
set TOP XGCDWrapper;
set CLOCK_PERIOD 2.75;
set CLKNAME clk;

# Setup
set_part $PART;
read_verilog $SRC;
set_property file_type SystemVerilog [ get_files ];

# Synthesize
synth_design -top $TOP

# Set constraints
create_clock -period $CLOCK_PERIOD -name $CLKNAME [get_ports $CLKNAME]

set_input_delay -clock $CLKNAME 0 [all_inputs]
set_output_delay -clock $CLKNAME 0 [all_outputs]

group_path -weight 2 -name critical -through gcd/*_csa_bezout_inter/*_odd_delta_update_*/u_*
group_path -weight 2 -name critical_x -through gcd/*_csa_bezout_inter/u_*

set_disable_timing [get_cells jtag_wrapper/*]

# Reporting post synth
set WRITEDIR reports/post-syn
file mkdir $WRITEDIR
write_checkpoint -force $WRITEDIR/post-syn
report_timing -file $WRITEDIR/timing.rpt
report_timing_summary -file $WRITEDIR/timing-summary.rpt
report_utilization -file $WRITEDIR/util-summary.rpt
report_utilization -hierarchical -file $WRITEDIR/util-hier-summary.rpt

# Optimize 
opt_design
power_opt_design

# Reporting post optimize
set WRITEDIR reports/post-opt
file mkdir $WRITEDIR
write_checkpoint -force $WRITEDIR/post-opt
report_timing -file $WRITEDIR/timing.rpt
report_timing_summary -file $WRITEDIR/timing-summary.rpt
report_utilization -file $WRITEDIR/util-summary.rpt
report_utilization -hierarchical -file $WRITEDIR/util-hier-summary.rpt

# set drc.disableLUTOverUtilError 1

# Place and Physical Optimizations
place_design

set WRITEDIR reports/post-place-only
file mkdir $WRITEDIR
write_checkpoint -force $WRITEDIR/post-place-only
report_utilization -file $WRITEDIR/util-summary.rpt
report_utilization -hierarchical -file $WRITEDIR/util-hier-summary.rpt

phys_opt_design

# Reporting post place
set WRITEDIR reports/post-place
file mkdir $WRITEDIR
write_checkpoint -force $WRITEDIR/post-place
report_timing -file $WRITEDIR/timing.rpt
report_timing_summary -file $WRITEDIR/timing-summary.rpt
report_utilization -file $WRITEDIR/util-summary.rpt
report_utilization -hierarchical -file $WRITEDIR/util-hier-summary.rpt

# Route
route_design

# Reporting post route
set WRITEDIR reports/post-route
file mkdir $WRITEDIR
write_checkpoint -force $WRITEDIR/post-route
report_timing -file $WRITEDIR/timing.rpt
report_timing_summary -file $WRITEDIR/timing-summary.rpt
report_utilization -file $WRITEDIR/util-summary.rpt
report_utilization -hierarchical -file $WRITEDIR/hier-summary.rpt

exit

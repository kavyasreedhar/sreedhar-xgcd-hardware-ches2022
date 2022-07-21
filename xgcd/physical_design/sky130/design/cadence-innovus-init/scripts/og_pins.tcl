#=========================================================================
# pin-assignments.tcl
#=========================================================================
# The ports of this design become physical pins along the perimeter of the
# design. The commands below will spread the pins along the left and right
# perimeters of the core area. This will work for most designs, but a
# detail-oriented project should customize or replace this section.
#
# Author : Christopher Torng
# Date   : March 26, 2018

#-------------------------------------------------------------------------
# Pin Assignments
#-------------------------------------------------------------------------

# Take all ports and split into halves

# set all_ports       [dbGet top.terms.name -v *clk*]

#set num_ports       [llength $all_ports]
#set half_ports_idx  [expr $num_ports / 2]

#set pins_left_half  [lrange $all_ports 0               [expr $half_ports_idx - 1]]
#set pins_right_half [lrange $all_ports $half_ports_idx [expr $num_ports - 1]     ]

# Take all clock ports and place them center-left

#set clock_ports     [dbGet top.terms.name *clk*]
#set half_left_idx   [expr [llength $pins_left_half] / 2]

#if { $clock_ports != 0 } {
#  for {set i 0} {$i < [llength $clock_ports]} {incr i} {
#    set pins_left_half \
#      [linsert $pins_left_half $half_left_idx [lindex $clock_ports $i]]
#  }
#}


#set right_ports []
#for {set i 0} {$i < 15} {incr i} {
#  set right_ports [linsert $right_ports 0 [dbGet top.terms.name io_in[$i]]]
#  set right_ports [linsert $right_ports 0 [dbGet top.terms.name io_out[$i]]]
#  set right_ports [linsert $right_ports 0 [dbGet top.terms.name io_oeb[$i]]]
#}

#set top_ports []
#for {set i 15} {$i < 23} {incr i} {
#  set top_ports [linsert $top_ports 0 [dbGet top.terms.name io_in[$i]]]
#  set top_ports [linsert $top_ports 0 [dbGet top.terms.name io_out[$i]]]
#  set top_ports [linsert $top_ports 0 [dbGet top.terms.name io_oeb[$i]]]
#}

#set unused_ports []
#for {set i 23} {$i < 38} {incr i} {
#  set unused_ports [linsert $unused_ports 0 [dbGet top.terms.name io_in[$i]]]
#  set unused_ports [linsert $unused_ports 0 [dbGet top.terms.name io_out[$i]]]
#  set unused_ports [linsert $unused_ports 0 [dbGet top.terms.name io_oeb[$i]]]
#}
#

#set in_io [dbGet top.terms.name io_in*]
#set out_io [dbGet top.terms.name io_out*]
#set oeb_io [dbGet top.terms.name io_oeb*]

#set right_ports []
#for {set i 0} {$i < 15} {incr i} {
#  set right_ports [linsert $right_ports 0 [dbGet top.terms.name io_in[$i]]]
#  set right_ports [linsert $right_ports 0 [dbGet top.terms.name io_out[$i]]]
#  set right_ports [linsert $right_ports 0 [dbGet top.terms.name io_oeb[$i]]]
#}
# Spread the pins evenly across the left and right sides of the block



set ports_layer M4

editPin -layer $ports_layer -pin [list io_in[0] io_oeb[0] io_out[0] io_in[1] io_oeb[1] io_out[1] io_in[2] io_oeb[2] io_out[2] io_in[3] io_oeb[3] io_out[3] io_in[4] io_oeb[4] io_out[4] io_in[5] io_oeb[5] io_out[5] io_in[6] io_oeb[6] io_out[6] io_in[7] io_oeb[7] io_out[7] io_in[8] io_oeb[8] io_out[8] io_in[9] io_oeb[9] io_out[9] io_in[10] io_oeb[10] io_out[10] io_in[11] io_oeb[11] io_out[11] io_in[12] io_oeb[12] io_out[12] io_in[13] io_oeb[13] io_out[13] io_in[14] io_oeb[14] io_out[14]] -side RIGHT -spreadType SIDE -spreadDirection CounterClockwise
editPin -layer $ports_layer -pin [list io_in[27] io_oeb[27] io_out[27] io_in[28] io_oeb[28] io_out[28] io_in[29] io_oeb[29] io_out[29] clk rst_n io_in[30] io_oeb[30] io_out[30] io_in[31] io_oeb[31] io_out[31] io_in[32] io_oeb[32] io_out[32]] -side LEFT -spreadType SPREAD -spreadDirection CounterClockwise
editPin -layer $ports_layer -pin [list io_in[15] io_oeb[15] io_out[15] io_in[16] io_oeb[16] io_out[16] io_in[17] io_oeb[17] io_out[17] io_in[18] io_oeb[18] io_out[18] io_in[19] io_oeb[19] io_out[19] io_in[20] io_oeb[20] io_out[20] io_in[21] io_oeb[21] io_out[21] io_in[22] io_oeb[22] io_out[22] io_in[23] io_oeb[23] io_out[23] io_in[24] io_oeb[24] io_out[24] io_in[25] io_oeb[25] io_out[25] io_in[26] io_oeb[26] io_out[26] io_in[33] io_oeb[33] io_out[33] io_in[34] io_oeb[34] io_out[34] io_in[35] io_oeb[35] io_out[35] io_in[36] io_oeb[36] io_out[36] io_in[37] io_oeb[37] io_out[37]] -side TOP -spreadType SIDE

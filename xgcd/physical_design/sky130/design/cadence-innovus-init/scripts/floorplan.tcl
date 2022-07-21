#=========================================================================
# floorplan.tcl
#=========================================================================
# Author : Christopher Torng
# Date   : March 26, 2018

#-------------------------------------------------------------------------
# Floorplan variables
#-------------------------------------------------------------------------

# Set the floorplan to target a reasonable placement density with a good
# aspect ratio (height:width). An aspect ratio of 2.0 here will make a
# rectangular chip with a height that is twice the width.

#set core_aspect_ratio   1.00; # Aspect ratio 1.0 for a square chip
#set core_density_target 0.50; # Placement density of 70% is reasonable

# Make room in the floorplan for the core power ring

set pwr_net_list {vssa2 vdda2 vssa1 vdda1 vssd2 vccd2 VSS VDD}; # List of power nets in the core power ring

set M1_min_width   [dbGet [dbGetLayerByZ 1].minWidth]
set M1_min_spacing [dbGet [dbGetLayerByZ 1].minSpacing]

set savedvars(p_ring_width)   3.0;   # Arbitrary!
set savedvars(p_ring_spacing) 1.7; # Arbitrary!

# Core bounding box margins

#set core_margin_t [expr (7 * ($savedvars(p_ring_width) + $savedvars(p_ring_spacing))) + $savedvars(p_ring_width)]
#set core_margin_b [expr (7 * ($savedvars(p_ring_width) + $savedvars(p_ring_spacing))) + $savedvars(p_ring_width)]
#set core_margin_r [expr (7 * ($savedvars(p_ring_width) + $savedvars(p_ring_spacing))) + $savedvars(p_ring_width)]
#set core_margin_l [expr (7 * ($savedvars(p_ring_width) + $savedvars(p_ring_spacing))) + $savedvars(p_ring_width)]

#floorPlan -s 2920 3520 \
#             $core_margin_l $core_margin_b $core_margin_r $core_margin_t

#-------------------------------------------------------------------------
# Floorplan
#-------------------------------------------------------------------------

# Calling floorPlan with the "-r" flag sizes the floorplan according to
# the core aspect ratio and a density target (70% is a reasonable
# density).
#

set core_margin_l [expr (6.980 + (8 * 3.0) + (7 * 1.7))]
set core_margin_r [expr (6.520 + (8 * 3.0) + (7 * 1.7))]
set core_margin_t [expr (1.620 + (8 * 3.0) + (7 * 1.7))]
set core_margin_b [expr (1.620 + (8 * 3.0) + (7 * 1.7))]

floorPlan -s 2920 3520 \
             $core_margin_l $core_margin_b $core_margin_r $core_margin_t
#floorPlan -r $core_aspect_ratio $core_density_target \
             $core_margin_l $core_margin_b $core_margin_r $core_margin_t

setFlipping s

# Use automatic floorplan synthesis to pack macros (e.g., SRAMs) together

planDesign

createRouteBlk -exceptpgnet -box [list 0.0 0.0 [expr $core_margin_l + 2.4] [expr 3520 + $core_margin_b + $core_margin_t]] -layer all -name left_blk
createRouteBlk -exceptpgnet -box [list 0.0 0.0 [expr 2920 + $core_margin_l + $core_margin_r] [expr $core_margin_b + 2.4]] -layer all -name bot_blk
createRouteBlk -exceptpgnet -box [list [expr 2920 + $core_margin_l - 2.48] 0.0 [expr 2920 + $core_margin_l + $core_margin_r] [expr $core_margin_b + 3520 + $core_margin_t]] -layer all -name right_blk
createRouteBlk -exceptpgnet -box [list 0.0 [expr $core_margin_b + 3520 - 2.4] [expr 2920 + $core_margin_l + $core_margin_r] [expr $core_margin_b + 3520 + $core_margin_t]] -layer all -name top_blk 
#createRouteBlk -exceptpgnet -box [list 0.0 0.0 $core_margin_l [expr 3520 + $core_margin_b + $core_margin_t]] -layer all -name left_blk
#createRouteBlk -exceptpgnet -box [list 0.0 0.0 [expr 2920 + $core_margin_l + $core_margin_r] $core_margin_b] -layer all -name bot_blk
#createRouteBlk -exceptpgnet -box [list [expr 2920 + $core_margin_l] 0.0 [expr 2920 + $core_margin_l + $core_margin_r] [expr $core_margin_b + 3520 + $core_margin_t]] -layer all -name right_blk
#createRouteBlk -exceptpgnet -box [list 0.0 [expr $core_margin_b + 3520] [expr 2920 + $core_margin_l + $core_margin_r] [expr $core_margin_b + 3520 + $core_margin_t]] -layer all -name top_blk 

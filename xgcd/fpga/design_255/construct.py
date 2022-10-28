#! /usr/bin/env python
#=========================================================================
# construct.py
#=========================================================================
# Author : Kavya Sreedhar
# Date   : July 21, 2022
#

import os
import sys

from mflowgen.components import Graph, Step

def construct():

  g = Graph()

  #-----------------------------------------------------------------------
  # Parameters
  #-----------------------------------------------------------------------

  parameters = {
    'construct_path'        : __file__,
    'design_name'           : 'XGCDWrapper',
    'bit_length'            : 255,
    'reduction_factor_even' : 2,
    'reduction_factor_odd'  : 4,
    'constant_time_support' : 0,
    'clock_period'          : 2.22,
    'fpga_part'             : 'xczu7eg-ffvf1517-3-e',
    'topographical'         : True,
    'hold_target_slack'     : 0.005,
    'setup_target_slack'    : 0.120,
  }

  jtag_cfg_bus_width = (parameters['bit_length'] + 5) * 2 + 1
  parameters['jtag_cfg_bus_width'] = jtag_cfg_bus_width

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # Custom steps

  info            = Step( 'info',                          default=True )
  rtl             = Step( this_dir + '/rtl'                             )
  fpga_synth_pnr  = Step( this_dir + '/fpga_synth_pnr'                  )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info            )
  g.add_step( rtl             )
  g.add_step( fpga_synth_pnr  )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Dynamically add edges

  # Connect by name

  g.connect_by_name( rtl,             fpga_synth_pnr              )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  return g

if __name__ == '__main__':
  g = construct()
  g.plot()

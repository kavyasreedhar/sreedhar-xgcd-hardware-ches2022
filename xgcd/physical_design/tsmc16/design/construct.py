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

  adk_name = 'tsmc16'
  adk_view = 'multivt'

  parameters = {
    'construct_path'     : __file__,
    'design_name'        : 'XGCDWrapper',
    'bit_length'         : 1024,
    'reduction_factor_even' : 8,
    'reduction_factor_odd': 4,
    'constant_time_support': 0,
    'DW_ALL_PATH'        : '/cad/synopsys/dc_shell/latest/dw/sim_ver',
    'clock_period'       : 0.25,
    'adk'                : adk_name,
    'adk_view'           : adk_view,
    'topographical'      : True,
    'hold_target_slack'  : 0.005,
    'setup_target_slack' : 0.020,
    'DW_ALL_PATH': '/cad/synopsys/dc_shell/latest/dw/sim_ver',
  }

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step

  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps

  rtl         = Step( this_dir + '/rtl' )
  constraints = Step( this_dir + '/constraints' )

  # Default steps

  info        = Step( 'info', default=True )
  dc          = Step( this_dir + '/synopsys-dc-synthesis' )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info            )
  g.add_step( rtl             )
  g.add_step( constraints     )
  g.add_step( dc              )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Connect by name

  g.connect_by_name( adk,         dc )
  g.connect_by_name( rtl,         dc )
  g.connect_by_name( constraints, dc )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  return g

if __name__ == '__main__':
  g = construct()
  g.plot()

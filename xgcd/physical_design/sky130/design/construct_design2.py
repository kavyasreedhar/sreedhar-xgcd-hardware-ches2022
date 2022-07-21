#! /usr/bin/env python
#=========================================================================
# construct.py
#=========================================================================

import os
import sys

from mflowgen.components import Graph, Step

def construct():

  g = Graph()

  #-----------------------------------------------------------------------
  # Parameters
  #-----------------------------------------------------------------------

  adk_name = 'skywater-130nm'
  adk_view = 'view-standard'

  parameters = {
    'construct_path' : __file__,
    'design_name'    : 'XGCDWrapper',
    'bit_length'     : 255,
    'reduction_factor_even' : 2,
    'reduction_factor_odd': 4,
    'constant_time_support': 1,
    'DW_ALL_PATH': '/cad/synopsys/dc_shell/latest/dw/sim_ver',
    'clock_period'   : 3.0,
    'adk'            : adk_name,
    'adk_view'       : adk_view,
    'topographical'  : True,
    'hold_target_slack': 0.005,
    'setup_target_slack': 0.120,
  }

  jtag_cfg_bus_width = (parameters['bit_length'] + 5) * 2 + 1
  parameters['jtag_cfg_bus_width'] = jtag_cfg_bus_width

  #-----------------------------------------------------------------------
  # Create nodes
  #-----------------------------------------------------------------------

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  # ADK step

  g.set_adk( adk_name )
  adk = g.get_adk_step()

  # Custom steps

  rtl             = Step( this_dir + '/rtl'                             )
  constraints     = Step( this_dir + '/constraints'                     )
  dc              = Step( this_dir + '/synopsys-dc-synthesis',          )
  init            = Step( this_dir + '/cadence-innovus-init',           )

  # Power node is custom because power and gnd pins are named differently in
  # the standard cells compared to the default node, and the layer numbering is
  # different because of li layer, the default assumes metal 1 is the lowest
  # layer

  power           = Step( this_dir + '/cadence-innovus-power'           )

  # Signoff is custom because it has to output def that the default step does
  # not do. This is because we use the def instead of gds for generating spice
  # from layout for LVS

  decapsignoff    = Step( this_dir + '/decapsignoff')

  # Default steps

  info            = Step( 'info',                          default=True )

  # Need to use clone if you want to instantiate the same node more than once
  # in your graph but configure it differently, for example, RTL simulation and
  # gate-level simulation use the same VCS node


  iflow           = Step( 'cadence-innovus-flowsetup',     default=True )
  place           = Step( 'cadence-innovus-place',         default=True )
  cts             = Step( 'cadence-innovus-cts',           default=True )
  postcts_hold    = Step( 'cadence-innovus-postcts_hold',  default=True )
  route           = Step( 'cadence-innovus-route',         default=True )
  postroute       = Step( 'cadence-innovus-postroute',     default=True )
  gdsmerge        = Step( 'mentor-calibre-gdsmerge',       default=True )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info            )
  g.add_step( rtl             )
  g.add_step( constraints     )
  g.add_step( dc              )
  g.add_step( iflow           )
  g.add_step( init            )
  g.add_step( power           )
  g.add_step( place           )
  g.add_step( cts             )
  g.add_step( postcts_hold    )
  g.add_step( route           )
  g.add_step( postroute       )
  g.add_step( decapsignoff    )
  g.add_step( gdsmerge        )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Dynamically add edges

  # Connect by name

  g.connect_by_name( adk,             dc              )
  g.connect_by_name( adk,             iflow           )
  g.connect_by_name( adk,             init            )
  g.connect_by_name( adk,             power           )
  g.connect_by_name( adk,             place           )
  g.connect_by_name( adk,             cts             )
  g.connect_by_name( adk,             postcts_hold    )
  g.connect_by_name( adk,             route           )
  g.connect_by_name( adk,             postroute       )
  g.connect_by_name( adk,             decapsignoff    )
  g.connect_by_name( adk,             gdsmerge        )

  g.connect_by_name( rtl,             dc              )
  g.connect_by_name( constraints,     dc              )

  g.connect_by_name( dc,              iflow           )
  g.connect_by_name( dc,              init            )
  g.connect_by_name( dc,              power           )
  g.connect_by_name( dc,              place           )
  g.connect_by_name( dc,              cts             )

  g.connect_by_name( iflow,           init            )
  g.connect_by_name( iflow,           power           )
  g.connect_by_name( iflow,           place           )
  g.connect_by_name( iflow,           cts             )
  g.connect_by_name( iflow,           postcts_hold    )
  g.connect_by_name( iflow,           route           )
  g.connect_by_name( iflow,           postroute       )
  g.connect_by_name( iflow,           decapsignoff    )

  # Core place and route flow
  g.connect_by_name( init,            power           )
  g.connect_by_name( power,           place           )
  g.connect_by_name( place,           cts             )
  g.connect_by_name( cts,             postcts_hold    )
  g.connect_by_name( postcts_hold,    route           )
  g.connect_by_name( route,           postroute       )
  g.connect_by_name( postroute,       decapsignoff    )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  g.update_params( parameters )

  return g

if __name__ == '__main__':
  g = construct()
  g.plot()

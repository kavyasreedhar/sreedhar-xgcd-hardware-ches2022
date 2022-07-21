# Write netlist for LVS
#
# Exclude physical cells that have no devices in them (or else LVS will
# have issues). Specifically for filler cells, the extracted layout will
# not have any trace of the fillers because there are no devices in them.
# Meanwhile, the schematic generated from the netlist will show filler
# cells instances with VDD/VSS ports, and this will cause LVS to flag a
# "mismatch" with the layout.

foreach x $ADK_LVS_EXCLUDE_CELL_LIST {
  append lvs_exclude_list [dbGet -u -e top.insts.cell.name $x] " "
}

# Typically we would exclude cells, but we are not in this case,
# since Magic creates abstract views for all cells (incl. filler)
saveNetlist -excludeLeafCell                   \
            -flat                             \
           -phys                              \
           -excludeCellInst $lvs_exclude_list \
           exclude.lvs.v

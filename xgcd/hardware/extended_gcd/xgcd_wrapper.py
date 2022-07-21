import argparse
import os
import kratos as k
from kratos import *

from xgcd.hardware.extended_gcd.xgcd_top import XGCDTop
from xgcd.hardware.jtag.jtag_wrapper import JtagWrapper
from xgcd.hardware.AhaResetSync import AhaResetSync


# top level wiring for GCD Unit, JTAG, and ResetSync
# this is the top level module
# port names correspond to Caravel I/O names
class XGCDWrapper(Generator):
    def __init__(self,
                 bit_length=1024,
                 DW=True,
                 shift_factor_a=4,
                 shift_factor_b=4,
                 shift_factor_b_odd=4,
                 constant_time_support=False):
        super().__init__(f"XGCDWrapper", debug=True)

        self.bit_length = bit_length
        self.DW = DW
        self.shift_factor_a = shift_factor_a
        self.shift_factor_b = shift_factor_b
        self.shift_factor_b_odd = shift_factor_b_odd
        self.constant_time_support = constant_time_support

        # unused inputs
        self.wb_clk_i = self.input("wb_clk_i", 1)
        self.wb_rst_i = self.input("wb_rst_i", 1)
        self.wbs_stb_i = self.input("wbs_stb_i", 1)
        self.wbs_cyc_i = self.input("wbs_cyc_i", 1)
        self.wbs_we_i = self.input("wbs_we_i", 1)
        self.wbs_sel_i = self.input("wbs_sel_i", 4)
        self.wbs_dat_i = self.input("wbs_dat_i", 32)
        self.wbs_adr_i = self.input("wbs_adr_i", 32)
        self.la_data_in = self.input("la_data_in", 128)
        self.la_oenb = self.input("la_oenb", 128)
        self.analog_io = self.input("analog_io", 29)
        self.user_clock2 = self.input("user_clock2", 1)

        self.io_in = self.input("io_in", 38)
        self.io_out = self.output("io_out", 38)
        self.io_oeb = self.output("io_oeb", 38)

        self.clk = self.clock("clk")
        self.rst_n = self.reset("rst_n", 1)

        # unused outputs grounded
        self.wbs_ack_o = self.output("wbs_ack_o", 1)
        self.wire(self.wbs_ack_o, 0)

        self.wbs_dat_o = self.output("wbs_dat_o", 32)
        self.wire(self.wbs_dat_o, 0)

        self.la_data_out = self.output("la_data_out", 128)
        self.wire(self.la_data_out, 0)

        self.user_irq = self.output("user_irq", 3)
        self.wire(self.user_irq, 0)

        # modules
        self.jtag_wrapper = JtagWrapper(self.bit_length)
        self.add_child("jtag_wrapper", self.jtag_wrapper)

        self.gcd = XGCDTop(bit_length=self.bit_length,
                            debug_print=False,
                            DW=self.DW,
                            final_clock_factor=4,
                            start_clock_factor=2,
                            check_except=False,
                            track_cycle_count=True,
                            shift_factor_a=self.shift_factor_a,
                            shift_factor_b=self.shift_factor_b,
                            shift_factor_b_odd=self.shift_factor_b_odd,
                            constant_time_support=self.constant_time_support)
                            
        self.add_child("gcd", self.gcd)

        # Caravel user project wrapper to jtag_wrapper
        # inputs
        self.wire(self.io_oeb[27], 1)
        self.wire(self.jtag_wrapper.ports.trst_n, self.io_in[27])
        
        self.wire(self.io_oeb[29], 1)
        self.wire(self.jtag_wrapper.ports.tck, self.io_in[29])

        self.wire(self.io_oeb[32], 1)
        self.wire(self.jtag_wrapper.ports.tms, self.io_in[32])

        self.wire(self.io_oeb[28], 1)
        self.wire(self.jtag_wrapper.ports.tdi, self.io_in[28])

        # outputs
        self.wire(self.io_oeb[13], 0)
        self.wire(self.jtag_wrapper.ports.tdo, self.io_out[13])

        # Caravel user project wrapper to GCD
        # analog_io 23 is connected to clk
        # clock input enable (not actually needed)
        self.wire(self.io_oeb[23], 1)
        self.wire(self.gcd.ports.clk, self.clk)

        # reset input enable
        self.wire(self.io_oeb[31], 1)

        # reset synchronizer for system reset
        self.reset_sync = AhaResetSync()
        self.add_child("reset_sync",
                       self.reset_sync,
                       CLK=self.clk,
                       Dn=self.rst_n)
        
        self.wire(self.gcd.ports.rst_n, k.util.async_reset(self.reset_sync.ports.Qn))

        for i in range(0, 12):
            self.wire(self.io_oeb[i], 0)
        self.wire(self.io_out[11, 0], self.gcd.ports.total_cycle_count)

        used = [23, 31, 28, 32, 29, 27, 13]
        inputs = [23, 31, 28, 32, 29, 27]
        for i in range(12):
            used.append(i)
        
        all_io = [i for i in range(38)]
        unused = []
        for i in all_io:
            if i not in used:
                unused.append(i)
        
        for x in unused:
            self.wire(self.io_oeb[x], 0)
        
        for x in unused + inputs:
            self.wire(self.io_out[x], 0)

        # GCD and jtag_wrapper
        self.wire(self.jtag_wrapper.ports.A, self.gcd.ports.A)
        self.wire(self.jtag_wrapper.ports.B, self.gcd.ports.B)
        self.wire(self.jtag_wrapper.ports.bezout_a, self.gcd.ports.bezout_a)
        self.wire(self.jtag_wrapper.ports.bezout_b, self.gcd.ports.bezout_b)
        self.wire(self.jtag_wrapper.ports.clk_en, self.gcd.ports.clk_en)
        self.wire(self.jtag_wrapper.ports.clk_in, self.clk)
        self.wire(self.jtag_wrapper.ports.done, self.gcd.ports.done)
        self.wire(self.jtag_wrapper.ports.rst_n, k.util.async_reset(self.reset_sync.ports.Qn))
        self.wire(self.jtag_wrapper.ports.start, self.gcd.ports.start)
        self.wire(self.jtag_wrapper.ports.constant_time, self.gcd.ports.constant_time)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Extended GCD hardware generator")
    parser.add_argument('--bit_length', type=int, default=1024, help="bitwidth for XGCD")
    parser.add_argument('--constant_time_support', default=False, action="store_true", help="constant-time XGCD (worst-case number of iterations)")
    parser.add_argument('--reduction_factor_even', type=int, default=8, help="Factor of 2 to reduce b by each cycle if even")
    parser.add_argument('--reduction_factor_odd', type=int, default=4, help="Factor of 2 to reduce b when odd by each cycle if even")
    parser.add_argument('--csa_handwritten', default=False, action="store_true", help="if used, use CSA stub instead of DesignWare CSA module")
    parser.add_argument('--output', default="XGCDWrapper.v", help="name of output Verilog file")
    args = parser.parse_args()

    print("XGCDWrapper Verilog Generation Parameter Summary: ")
    print(args)

    file_name = args.output

    print()
    print(f"Generating XGCDWrapper at {file_name}")

    gcd_wrapper = XGCDWrapper(bit_length=args.bit_length,
                              DW=(not args.csa_handwritten),
                              shift_factor_a=args.reduction_factor_even,
                              shift_factor_b=args.reduction_factor_even,
                              shift_factor_b_odd=args.reduction_factor_odd,
                              constant_time_support=args.constant_time_support)

    verilog(gcd_wrapper, filename=file_name)

    top_path = os.getenv("TOP")

    # add AhaResetSync verilog module to XGCDWrapper file since it is
    # set as an external module
    with open(f"{top_path}/xgcd/hardware/AhaResetSync.v") as reset_file:
        reset_lines = reset_file.readlines()
        with open(file_name, "a+") as wrapper:
            for line in reset_lines:
                wrapper.write(line)

import kratos as k
from kratos import *
import math
import argparse

from xgcd.hardware.extended_gcd.update_bezout import Update_Bezout
from xgcd.hardware.extended_gcd.post_processing import PostProcessing
from xgcd.hardware.extended_gcd.termination_condition import TerminationCondition
from xgcd.hardware.extended_gcd.pre_processing import PreProcessing
from xgcd.hardware.extended_gcd.update_a_b import Update_a_b

from xgcd.hardware.csa import *


class XGCDTop(Generator):
    def __init__(self,
                 bit_length,
                 debug_print=False,
                 DW=True,
                 final_clock_factor=4,
                 start_clock_factor=2,
                 check_except=False,
                 track_cycle_count=True,
                 cycle_count_bit_width=12,
                 shift_factor_a=4,
                 shift_factor_b=4,
                 shift_factor_b_odd=4,
                 constant_time_support=False,
                 add_clk_en=True):
        super().__init__(f"XGCDTop", debug=True)

        print()
        print(f"Generating {bit_length}-bit XGCD...")
        print(f"- with{'out' if constant_time_support is False else ''} constant-time-support")
        if DW:
            print("- with DesignWare CSA module")
        else:
            print("- with handwritten CSA module (NOT DesignWare CSA module)")

        # PARAMETERS
        self.bit_length = bit_length
        self.debug_print = debug_print
        # use synopsys DC DW modules or genus CW modules for CSA
        self.DW = DW
        self.inter_bit_length = self.bit_length + 5
        self.bit_length_msb = self.inter_bit_length - 1
        self.final_clock_factor = final_clock_factor
        self.start_clock_factor = start_clock_factor
        self.track_cycle_count = track_cycle_count
        self.cycle_count_bit_width = cycle_count_bit_width
        self.add_clk_en = True
        
        self.shift_factor = 4
        self.shift_factor_a = shift_factor_a
        self.shift_factor_b = shift_factor_b
        self.shift_factor_b_odd = shift_factor_b_odd
        assert self.shift_factor_a % 2 == 0, "shift_factor_a param must be divisible by 2"
        assert self.shift_factor_b % 2 == 0, "shift_factor_b param must be divisible by 2"
        assert self.shift_factor_b_odd % 2 == 0

        self.four_shift_factor = self.shift_factor_a >= 4 or \
                                 self.shift_factor_b >= 4 or \
                                 self.shift_factor_b_odd >= 4

        self.eight_shift_factor = self.shift_factor_a >= 8 or \
                                  self.shift_factor_b >= 8 or \
                                  self.shift_factor_b_odd >= 8

        self.constant_time_support = constant_time_support
        self.delta_msb = max(1, clog2(self.bit_length))

        # I/O
        self.clk = self.clock("clk")
        self.rst_n = self.reset("rst_n", 1)

        # if self.constant_time_support:
        # wire to 0 for non constant_time_support
        # (keep as input for standard JTAG interface)
        self.constant_time = self.input("constant_time", 1)

        # begin computation
        self.start = self.input("start", 1)
        # clk_en is also an input added by a pass at the end

        # Inputs to find Bezout coefficients for i.e.
        # bezout_a * A + bezout_b * B = gcd(A, B)
        self.A = self.input("A", self.bit_length)
        self.B = self.input("B", self.bit_length)
        
        # indicate when output is valid
        self.done = self.output("done", 1)

        # Bezout coefficients
        self.bezout_a = self.output("bezout_a", self.inter_bit_length)
        self.bezout_b = self.output("bezout_b", self.inter_bit_length)

        self.internal_start = self.var("internal_start", 1)

        if self.track_cycle_count:
            self.total_cycle_count = self.output("total_cycle_count", self.cycle_count_bit_width)
            self.total_cycle_count_inter = self.var("total_cycle_count_inter", self.cycle_count_bit_width)
            self.wire(self.total_cycle_count, self.total_cycle_count_inter)
            self.add_code(self.set_total_cycle_count_inter)

        # clk_en added below with kratos pass
        # END OF I/O

        self.done_inter = self.var("done_inter", 1)

        # a, b in CSA form
        self.a_carry = self.var("a_carry", self.inter_bit_length)
        self.b_carry = self.var("b_carry", self.inter_bit_length)
        self.a_sum = self.var("a_sum", self.inter_bit_length)
        self.b_sum = self.var("b_sum", self.inter_bit_length)

        # control variables approximating log_2(a) - log_2(b), 
        # log_2(a), log_2(b)
        self.delta = self.var("delta", self.delta_msb + 1, is_signed=True)

        # even reduction factor signals
        # support the option of different reduction factors for 
        # a and b, but swapping them result in similar results
        # (and also more parameterizations), so for simplicity,
        # functional model just keeps same reduction factor for
        # both a and b
        self.shift_a_4 = self.var("shift_a_4", 1)
        self.wire(self.shift_a_4, (self.shift_factor_a >= 4))
        self.shift_b_4 = self.var("shift_b_4", 1)
        self.wire(self.shift_b_4, (self.shift_factor_b >= 4))

        self.shift_a_8 = self.var("shift_a_8", 1)
        self.wire(self.shift_a_8, (self.shift_factor_a >= 8))
        self.shift_b_8 = self.var("shift_b_8", 1)
        self.wire(self.shift_b_8, (self.shift_factor_b >= 8))

        # odd reduction factor signals -- default is reduction factor of 4
        self.shift_b_2_odd = self.var("shift_b_2_odd", 1)
        self.wire(self.shift_b_2_odd, (self.shift_factor_b_odd == 2))
        self.shift_b_8_odd = self.var("shift_b_8_odd", 1)
        self.wire(self.shift_b_8_odd, (self.shift_factor_b_odd >= 8))
        
        self.even_case = self.var("even_case", 2)
        self.og_cycle = self.var("og_cycle", 1)
        self.compute = self.var("compute", 1)
        self.keep_start = self.var("keep_start", 1)
        
        # if a, b are divisble by 2 or 4
        self.ab_lsb_2 = self.var("ab_lsb_2", 1)
        self.a_after_lsb = self.var("a_after_lsb", 1)
        self.b_after_lsb = self.var("b_after_lsb", 1)
        self.a_after_lsb_2 = self.var("a_after_lsb_2", 1)
        self.b_after_lsb_2 = self.var("b_after_lsb_2", 1)
        self.a_after_lsb_3 = self.var("a_after_lsb_3", 1)
        self.b_after_lsb_3 = self.var("b_after_lsb_3", 1)
        self.ab_after_lsb_2 = self.var("ab_after_lsb_2", 1)
        self.ab_after_lsb_3 = self.var("ab_after_lsb_3", 1)
        self.a_minus_b_after_lsb_3 = self.var("a_minus_b_after_lsb_3", 1)
        self.ab_lsb_bl1 = self.var("ab_lsb_bl1", 1)

        self.update_a = self.var("update_a", 1)
        self.wire(self.update_a, ~self.a_after_lsb | (self.a_after_lsb & self.b_after_lsb & unsigned(~self.delta[self.delta_msb])))

        self.a_out_carry_preshift = self.var("a_out_carry_preshift", self.inter_bit_length)
        self.a_out_sum_preshift = self.var("a_out_sum_preshift", self.inter_bit_length)

        update_a_b = Update_a_b(self.bit_length,
                                self.inter_bit_length,
                                self.delta_msb,
                                self.DW,
                                self.debug_print)
        
        self.add_child("update_a_b",
                       update_a_b,
                       clk=self.clk,
                       rst_n=self.rst_n,
                       internal_start=self.internal_start,
                       compute=self.compute,
                       A=self.A,
                       B=self.B,
                       delta=self.delta,
                       even_case=self.even_case,
                       shift_a_4=self.shift_a_4,
                       shift_b_4=self.shift_b_4,
                       shift_a_8=self.shift_a_8,
                       shift_b_8=self.shift_b_8,
                       shift_b_2_odd=self.shift_b_2_odd,
                       shift_b_8_odd=self.shift_b_8_odd,
                       a_carry_out=self.a_carry,
                       b_carry_out=self.b_carry,
                       a_sum_out=self.a_sum,
                       b_sum_out=self.b_sum,
                       a_after_lsb_out=self.a_after_lsb,
                       b_after_lsb_out=self.b_after_lsb,
                       a_after_lsb_2_out=self.a_after_lsb_2,
                       b_after_lsb_2_out=self.b_after_lsb_2,
                       a_after_lsb_3_out=self.a_after_lsb_3,
                       b_after_lsb_3_out=self.b_after_lsb_3,
                       ab_after_lsb_2_out=self.ab_after_lsb_2,
                       ab_after_lsb_3_out=self.ab_after_lsb_3,
                       a_minus_b_after_lsb_3_out=self.a_minus_b_after_lsb_3,
                       a_out_carry_preshift=self.a_out_carry_preshift,
                       a_out_sum_preshift=self.a_out_sum_preshift)

        self.og_a = self.var("og_a", self.inter_bit_length)
        self.og_b = self.var("og_b", self.inter_bit_length)
        self.og_a2 = self.var("og_a2", self.inter_bit_length)
        self.og_b2 = self.var("og_b2", self.inter_bit_length)
        self.og_a3 = self.var("og_a3", self.inter_bit_length)
        self.og_b3 = self.var("og_b3", self.inter_bit_length)
        self.og_a4 = self.var("og_a4", self.inter_bit_length)
        self.og_b4 = self.var("og_b4", self.inter_bit_length)
        self.og_a5 = self.var("og_a5", self.inter_bit_length)
        self.og_b5 = self.var("og_b5", self.inter_bit_length)
        self.og_a6 = self.var("og_a6", self.inter_bit_length)
        self.og_b6 = self.var("og_b6", self.inter_bit_length)
        self.og_a7 = self.var("og_a7", self.inter_bit_length)
        self.og_b7 = self.var("og_b7", self.inter_bit_length)

        self.og_b_div4 = self.var("og_b_div4", 1)
        self.og_a_div4 = self.var("og_a_div4", 1)
        self.og_a_div4_plus = self.var("og_a_div4_plus", 1)

        if self.start_clock_factor == 0:
            self.start_clock = self.clk
        else:
            self.start_counter = self.var("start_counter", clog2(self.start_clock_factor))
            start_clock_ = self.var("start_clock_", 1)
            self.start_clock = k.util.clock(start_clock_)
            self.wire(start_clock_, k.util.clock(self.start_counter[clog2(self.start_clock_factor) - 1]))
            self.add_code(self.set_start_counter)

        og_vals = PreProcessing(inter_bit_length=self.inter_bit_length,
                                bit_length=self.bit_length,
                                four_shift_factor=self.four_shift_factor,
                                eight_shift_factor=self.eight_shift_factor,
                                debug_print=self.debug_print)
        self.add_child("og_vals",
                       og_vals,
                       clk=self.start_clock,
                       rst_n=self.rst_n,
                       A=self.A,
                       B=self.B,
                       start=self.internal_start,
                       og_cycle=self.og_cycle,
                       og_a=self.og_a, og_b=self.og_b,
                       og_a2=self.og_a2, og_b2=self.og_b2,
                       og_a3=self.og_a3, og_b3=self.og_b3,
                       og_a4=self.og_a4, og_b4=self.og_b4,
                       og_a5=self.og_a5, og_b5=self.og_b5,
                       og_a6=self.og_a6, og_b6=self.og_b6,
                       og_a7=self.og_a7, og_b7=self.og_b7,
                       og_a_div4=self.og_a_div4, og_b_div4=self.og_b_div4,
                       og_a_div4_plus=self.og_a_div4_plus)

        self.u_carry = self.var("u_carry", self.inter_bit_length)
        self.u_sum = self.var("u_sum", self.inter_bit_length)
        self.l_carry = self.var("l_carry", self.inter_bit_length)
        self.l_sum = self.var("l_sum", self.inter_bit_length)
        self.y_carry = self.var("y_carry", self.inter_bit_length)
        self.y_sum = self.var("y_sum", self.inter_bit_length)
        self.n_carry = self.var("n_carry", self.inter_bit_length)
        self.n_sum = self.var("n_sum", self.inter_bit_length)

        self.uu_y_after_lsb = self.var("uu_y_after_lsb", 1)
        self.uu_y_after_lsb_sub = self.var("uu_y_after_lsb_sub", 1)
        self.yu_y_after_lsb = self.var("yu_y_after_lsb", 1)
        self.yu_y_after_lsb_sub = self.var("yu_y_after_lsb_sub", 1)
        self.nu_y_after_lsb = self.var("nu_y_after_lsb", 1)
        self.nu_y_after_lsb_sub = self.var("nu_y_after_lsb_sub", 1)
        self.lu_y_after_lsb = self.var("lu_y_after_lsb", 1)
        self.lu_y_after_lsb_sub = self.var("lu_y_after_lsb_sub", 1)

        self.uupdated_u_y_after_lsb = self.var("uupdated_u_y_after_lsb", 1)
        self.uupdated_u_y_after_lsb_sub = self.var("uupdated_u_y_after_lsb_sub", 1)
        self.lupdated_u_y_after_lsb = self.var("lupdated_u_y_after_lsb", 1)
        self.lupdated_u_y_after_lsb_sub = self.var("lupdated_u_y_after_lsb_sub", 1)

        self.uu_y_after_lsb_2 = self.var("uu_y_after_lsb_2", 1)
        self.uu_y_after_lsb_2_sub = self.var("uu_y_after_lsb_2_sub", 1)
        self.yu_y_after_lsb_2 = self.var("yu_y_after_lsb_2", 1)
        self.yu_y_after_lsb_2_sub = self.var("yu_y_after_lsb_2_sub", 1)
        self.nu_y_after_lsb_2 = self.var("nu_y_after_lsb_2", 1)
        self.nu_y_after_lsb_2_sub = self.var("nu_y_after_lsb_2_sub", 1)
        self.lu_y_after_lsb_2 = self.var("lu_y_after_lsb_2", 1)
        self.lu_y_after_lsb_2_sub = self.var("lu_y_after_lsb_2_sub", 1)

        self.uupdated_u_y_after_lsb_2 = self.var("uupdated_u_y_after_lsb_2", 1)
        self.uupdated_u_y_after_lsb_2_sub = self.var("uupdated_u_y_after_lsb_2_sub", 1)
        self.lupdated_u_y_after_lsb_2 = self.var("lupdated_u_y_after_lsb_2", 1)
        self.lupdated_u_y_after_lsb_2_sub = self.var("lupdated_u_y_after_lsb_2_sub", 1)

        self.uinv_u_y_ogb_after_lsb_2 = self.var("uinv_u_y_ogb_after_lsb_2", 1)
        self.yinv_u_y_ogb_after_lsb_2 = self.var("yinv_u_y_ogb_after_lsb_2", 1)
        self.ninv_u_y_ogb_after_lsb_2 = self.var("ninv_u_y_ogb_after_lsb_2", 1)
        self.linv_u_y_ogb_after_lsb_2 = self.var("linv_u_y_ogb_after_lsb_2", 1)

        self.uupdated_inv_u_y_ogb_after_lsb_2 = self.var("uupdated_inv_u_y_ogb_after_lsb_2", 1)
        self.lupdated_inv_u_y_ogb_after_lsb_2 = self.var("lupdated_inv_u_y_ogb_after_lsb_2", 1)

        self.uinv_u_y_ogb_after_lsb_2_sub = self.var("uinv_u_y_ogb_after_lsb_2_sub", 1)
        self.yinv_u_y_ogb_after_lsb_2_sub = self.var("yinv_u_y_ogb_after_lsb_2_sub", 1)
        self.ninv_u_y_ogb_after_lsb_2_sub = self.var("ninv_u_y_ogb_after_lsb_2_sub", 1)
        self.linv_u_y_ogb_after_lsb_2_sub = self.var("linv_u_y_ogb_after_lsb_2_sub", 1)

        self.uupdated_inv_u_y_ogb_after_lsb_2_sub = self.var("uupdated_inv_u_y_ogb_after_lsb_2_sub", 1)
        self.lupdated_inv_u_y_ogb_after_lsb_2_sub = self.var("lupdated_inv_u_y_ogb_after_lsb_2_sub", 1)

        u_csa_bezout_inter = Update_Bezout(inter_bit_length=self.inter_bit_length,
                                           add_og_val=True, 
                                           initial_0=False, 
                                           u_l=True, 
                                           u_y=True,
                                           DW=self.DW,
                                           testing=True,
                                           debug_print=self.debug_print)

        self.add_child("u_csa_bezout_inter",
                       u_csa_bezout_inter,
                       clk=self.clk,
                       rst_n=self.rst_n,
                       start=self.internal_start,
                       done=self.compute,
                       a_lsb=self.a_after_lsb,
                       a_lsb_2=self.a_after_lsb_2,
                       a_lsb_3=self.a_after_lsb_3,
                       b_lsb=self.b_after_lsb,
                       delta_sign=unsigned(~self.delta[self.delta_msb]),
                       a_plus_b_4=self.ab_after_lsb_2,
                       a_plus_b_8=self.ab_after_lsb_3,
                       a_minus_b_8=self.a_minus_b_after_lsb_3,
                       shift_a_4=self.shift_a_4,
                       shift_a_8=self.shift_a_8,
                       shift_b_2_odd=self.shift_b_2_odd,
                       shift_b_8_odd=self.shift_b_8_odd,
                       u_y_after_lsb=self.uu_y_after_lsb,
                       u_y_after_lsb_sub=self.uu_y_after_lsb_sub,
                       u_y_after_lsb_2=self.uu_y_after_lsb_2,
                       u_y_after_lsb_2_sub=self.uu_y_after_lsb_2_sub,
                       updated_u_y_after_lsb=self.uupdated_u_y_after_lsb,
                       updated_u_y_after_lsb_sub=self.uupdated_u_y_after_lsb_sub,
                       updated_u_y_after_lsb_2=self.uupdated_u_y_after_lsb_2,
                       updated_u_y_after_lsb_2_sub=self.uupdated_u_y_after_lsb_2_sub,
                       inv_u_y_ogb_after_lsb_2=self.uinv_u_y_ogb_after_lsb_2,
                       updated_inv_u_y_ogb_after_lsb_2=self.uupdated_inv_u_y_ogb_after_lsb_2,
                       inv_u_y_ogb_after_lsb_2_sub=self.uinv_u_y_ogb_after_lsb_2_sub,
                       updated_inv_u_y_ogb_after_lsb_2_sub=self.uupdated_inv_u_y_ogb_after_lsb_2_sub,
                       og_b=self.og_b,
                       og_b2=self.og_b2,
                       og_b3=self.og_b3,
                       og_b4=self.og_b4,
                       og_b5=self.og_b5,
                       og_b6=self.og_b6,
                       og_b7=self.og_b7,
                       y_carry_in=self.y_carry,
                       y_sum_in=self.y_sum,
                       u_carry_out=self.u_carry,
                       u_sum_out=self.u_sum)
        
        l_csa_bezout_inter = Update_Bezout(inter_bit_length=self.inter_bit_length, 
                                           add_og_val=False, 
                                           initial_0=True, 
                                           u_l=True, 
                                           u_y=False,
                                           testing=True,
                                           DW=self.DW,
                                           debug_print=self.debug_print)
        self.add_child("l_csa_bezout_inter",
                       l_csa_bezout_inter,
                       clk=self.clk,
                       rst_n=self.rst_n,
                       start=self.internal_start,
                       done=self.compute,
                       a_lsb=self.a_after_lsb,
                       a_lsb_2=self.a_after_lsb_2,
                       a_lsb_3=self.a_after_lsb_3,
                       b_lsb=self.b_after_lsb,
                       delta_sign=unsigned(~self.delta[self.delta_msb]),
                       a_plus_b_4=self.ab_after_lsb_2,
                       a_plus_b_8=self.ab_after_lsb_3,
                       a_minus_b_8=self.a_minus_b_after_lsb_3,
                       shift_a_4=self.shift_a_4,
                       shift_a_8=self.shift_a_8,
                       shift_b_2_odd=self.shift_b_2_odd,
                       shift_b_8_odd=self.shift_b_8_odd,
                       u_y_after_lsb=self.lu_y_after_lsb,
                       u_y_after_lsb_sub=self.lu_y_after_lsb_sub,
                       u_y_after_lsb_2=self.lu_y_after_lsb_2,
                       u_y_after_lsb_2_sub=self.lu_y_after_lsb_2_sub,
                       updated_u_y_after_lsb=self.lupdated_u_y_after_lsb,
                       updated_u_y_after_lsb_sub=self.lupdated_u_y_after_lsb_sub,
                       updated_u_y_after_lsb_2=self.lupdated_u_y_after_lsb_2,
                       updated_u_y_after_lsb_2_sub=self.lupdated_u_y_after_lsb_2_sub,
                       inv_u_y_ogb_after_lsb_2=self.linv_u_y_ogb_after_lsb_2,
                       updated_inv_u_y_ogb_after_lsb_2=self.lupdated_inv_u_y_ogb_after_lsb_2,
                       inv_u_y_ogb_after_lsb_2_sub=self.linv_u_y_ogb_after_lsb_2_sub,
                       updated_inv_u_y_ogb_after_lsb_2_sub=self.lupdated_inv_u_y_ogb_after_lsb_2_sub,
                       og_b=self.og_a,
                       og_b2=self.og_a2,
                       og_b3=self.og_a3,
                       og_b4=self.og_a4,
                       og_b5=self.og_a5,
                       og_b6=self.og_a6,
                       og_b7=self.og_a7,
                       y_carry_in=self.n_carry,
                       y_sum_in=self.n_sum,
                       u_carry_out=self.l_carry,
                       u_sum_out=self.l_sum)

        y_csa_bezout_inter = Update_Bezout(inter_bit_length=self.inter_bit_length,
                                           add_og_val=True, 
                                           initial_0=True, 
                                           u_l=False, 
                                           u_y=True,
                                           DW=self.DW,
                                           testing=False,
                                           debug_print=self.debug_print)
        self.add_child("y_csa_bezout_inter",
                       y_csa_bezout_inter,
                       clk=self.clk,
                       rst_n=self.rst_n,
                       start=self.internal_start,
                       done=self.compute,
                       a_lsb=self.b_after_lsb,
                       a_lsb_2=self.b_after_lsb_2,
                       a_lsb_3=self.b_after_lsb_3,
                       b_lsb=self.a_after_lsb,
                       delta_sign=unsigned(self.delta[self.delta_msb]),
                       a_plus_b_4=self.ab_after_lsb_2,
                       a_plus_b_8=self.ab_after_lsb_3,
                       a_minus_b_8=self.a_minus_b_after_lsb_3,
                       shift_a_4=self.shift_b_4,
                       shift_a_8=self.shift_b_8,
                       shift_b_2_odd=self.shift_b_2_odd,
                       shift_b_8_odd=self.shift_b_8_odd,
                       u_y_after_lsb=self.yu_y_after_lsb,
                       u_y_after_lsb_sub=self.yu_y_after_lsb_sub,
                       u_y_after_lsb_2=self.yu_y_after_lsb_2,
                       u_y_after_lsb_2_sub=self.yu_y_after_lsb_2_sub,
                       updated_u_y_after_lsb=self.uupdated_u_y_after_lsb,
                       updated_u_y_after_lsb_sub=self.uupdated_u_y_after_lsb_sub,
                       updated_u_y_after_lsb_2=self.uupdated_u_y_after_lsb_2,
                       updated_u_y_after_lsb_2_sub=~self.uupdated_u_y_after_lsb_2_sub,
                       inv_u_y_ogb_after_lsb_2=self.yinv_u_y_ogb_after_lsb_2,
                       updated_inv_u_y_ogb_after_lsb_2=self.uupdated_inv_u_y_ogb_after_lsb_2,
                       inv_u_y_ogb_after_lsb_2_sub_switch=self.yinv_u_y_ogb_after_lsb_2_sub,
                       updated_inv_u_y_ogb_after_lsb_2_sub=self.uupdated_inv_u_y_ogb_after_lsb_2_sub,
                       og_b=self.og_b,
                       og_b2=self.og_b2,
                       og_b3=self.og_b3,
                       og_b4=self.og_b4,
                       og_b5=self.og_b5,
                       og_b6=self.og_b6,
                       og_b7=self.og_b7,
                       y_carry_in=self.u_carry,
                       y_sum_in=self.u_sum,
                       u_carry_out=self.y_carry,
                       u_sum_out=self.y_sum)

        n_csa_bezout_inter = Update_Bezout(inter_bit_length=self.inter_bit_length, 
                                           add_og_val=False, 
                                           initial_0=False, 
                                           u_l=False, 
                                           u_y=False,
                                           DW=self.DW,
                                           testing=False,
                                           debug_print=self.debug_print)
        self.add_child("n_csa_bezout_inter",
                       n_csa_bezout_inter,
                       clk=self.clk,
                       rst_n=self.rst_n,
                       start=self.internal_start,
                       done=self.compute,
                       a_lsb=self.b_after_lsb,
                       a_lsb_2=self.b_after_lsb_2,
                       a_lsb_3=self.b_after_lsb_3,
                       b_lsb=self.a_after_lsb,
                       delta_sign=unsigned(self.delta[self.delta_msb]),
                       a_plus_b_4=self.ab_after_lsb_2,
                       a_plus_b_8=self.ab_after_lsb_3,
                       a_minus_b_8=self.a_minus_b_after_lsb_3,
                       shift_a_4=self.shift_b_4,
                       shift_a_8=self.shift_b_8,
                       shift_b_2_odd=self.shift_b_2_odd,
                       shift_b_8_odd=self.shift_b_8_odd,
                       u_y_after_lsb=self.nu_y_after_lsb,
                       u_y_after_lsb_sub=self.nu_y_after_lsb_sub,
                       u_y_after_lsb_2=self.nu_y_after_lsb_2,
                       u_y_after_lsb_2_sub=self.nu_y_after_lsb_2_sub,
                       updated_u_y_after_lsb=self.lupdated_u_y_after_lsb,
                       updated_u_y_after_lsb_sub=self.lupdated_u_y_after_lsb_sub,
                       updated_u_y_after_lsb_2=self.lupdated_u_y_after_lsb_2,
                       updated_u_y_after_lsb_2_sub=~self.lupdated_u_y_after_lsb_2_sub,
                       inv_u_y_ogb_after_lsb_2=self.ninv_u_y_ogb_after_lsb_2,
                       updated_inv_u_y_ogb_after_lsb_2=self.lupdated_inv_u_y_ogb_after_lsb_2,
                       inv_u_y_ogb_after_lsb_2_sub_switch=self.ninv_u_y_ogb_after_lsb_2_sub,
                       updated_inv_u_y_ogb_after_lsb_2_sub=self.lupdated_inv_u_y_ogb_after_lsb_2_sub,
                       og_b=self.og_a,
                       og_b2=self.og_a2,
                       og_b3=self.og_a3,
                       og_b4=self.og_a4,
                       og_b5=self.og_a5,
                       og_b6=self.og_a6,
                       og_b7=self.og_a7,
                       y_carry_in=self.l_carry,
                       y_sum_in=self.l_sum,
                       u_carry_out=self.n_carry,
                       u_sum_out=self.n_sum)

        # avoid redundant computation between the Bezout coefficient modules
        # (u, l) and (y, n) share divisibility
        # (u, y) and (l, n) share sums/differences
        self.wire(l_csa_bezout_inter.ports.u_after_lsb, u_csa_bezout_inter.ports.u_after_lsb_out)
        self.wire(n_csa_bezout_inter.ports.u_after_lsb, y_csa_bezout_inter.ports.u_after_lsb_out)
        self.wire(l_csa_bezout_inter.ports.u_after_lsb_2, u_csa_bezout_inter.ports.u_after_lsb_2_out)
        self.wire(n_csa_bezout_inter.ports.u_after_lsb_2, y_csa_bezout_inter.ports.u_after_lsb_2_out)
        self.wire(l_csa_bezout_inter.ports.u_after_lsb_3, u_csa_bezout_inter.ports.u_after_lsb_3_out)
        self.wire(n_csa_bezout_inter.ports.u_after_lsb_3, y_csa_bezout_inter.ports.u_after_lsb_3_out)

        self.wire(u_csa_bezout_inter.ports.u_delta_update_add_carry_out, y_csa_bezout_inter.ports.u_delta_update_add_carry_out)
        self.wire(u_csa_bezout_inter.ports.u_delta_update_add_sum_out, y_csa_bezout_inter.ports.u_delta_update_add_sum_out)
        self.wire(u_csa_bezout_inter.ports.u_delta_update_sub_first_carry_out, y_csa_bezout_inter.ports.u_delta_update_sub_first_carry_out)
        self.wire(u_csa_bezout_inter.ports.u_delta_update_sub_first_sum_out, y_csa_bezout_inter.ports.u_delta_update_sub_first_sum_out)

        self.wire(u_csa_bezout_inter.ports.u_delta_update_add_carry_by_2_out, y_csa_bezout_inter.ports.u_delta_update_add_carry_by_2_out)
        self.wire(u_csa_bezout_inter.ports.u_delta_update_add_sum_by_2_out, y_csa_bezout_inter.ports.u_delta_update_add_sum_by_2_out)
        self.wire(u_csa_bezout_inter.ports.u_delta_update_sub_first_carry_by_2_out, y_csa_bezout_inter.ports.u_delta_update_sub_first_carry_by_2_out)
        self.wire(u_csa_bezout_inter.ports.u_delta_update_sub_first_sum_by_2_out, y_csa_bezout_inter.ports.u_delta_update_sub_first_sum_by_2_out)

        self.wire(u_csa_bezout_inter.ports.u_delta_update_add_ogb_by_2_carry_out, y_csa_bezout_inter.ports.u_delta_update_add_ogb_by_2_carry_out)
        self.wire(u_csa_bezout_inter.ports.u_delta_update_add_ogb_by_2_sum_out, y_csa_bezout_inter.ports.u_delta_update_add_ogb_by_2_sum_out)
        self.wire(u_csa_bezout_inter.ports.u_delta_update_sub_first_ogb_by_2_carry_out, y_csa_bezout_inter.ports.u_delta_update_sub_first_ogb_by_2_carry_out)
        self.wire(u_csa_bezout_inter.ports.u_delta_update_sub_first_ogb_by_2_sum_out, y_csa_bezout_inter.ports.u_delta_update_sub_first_ogb_by_2_sum_out)

        self.wire(l_csa_bezout_inter.ports.u_delta_update_add_carry_out, n_csa_bezout_inter.ports.u_delta_update_add_carry_out)
        self.wire(l_csa_bezout_inter.ports.u_delta_update_add_sum_out, n_csa_bezout_inter.ports.u_delta_update_add_sum_out)
        self.wire(l_csa_bezout_inter.ports.u_delta_update_sub_first_carry_out, n_csa_bezout_inter.ports.u_delta_update_sub_first_carry_out)
        self.wire(l_csa_bezout_inter.ports.u_delta_update_sub_first_sum_out, n_csa_bezout_inter.ports.u_delta_update_sub_first_sum_out)

        self.wire(l_csa_bezout_inter.ports.u_delta_update_add_carry_by_2_out, n_csa_bezout_inter.ports.u_delta_update_add_carry_by_2_out)
        self.wire(l_csa_bezout_inter.ports.u_delta_update_add_sum_by_2_out, n_csa_bezout_inter.ports.u_delta_update_add_sum_by_2_out)
        self.wire(l_csa_bezout_inter.ports.u_delta_update_sub_first_carry_by_2_out, n_csa_bezout_inter.ports.u_delta_update_sub_first_carry_by_2_out)
        self.wire(l_csa_bezout_inter.ports.u_delta_update_sub_first_sum_by_2_out, n_csa_bezout_inter.ports.u_delta_update_sub_first_sum_by_2_out)

        self.wire(l_csa_bezout_inter.ports.u_delta_update_add_ogb_by_2_carry_out, n_csa_bezout_inter.ports.u_delta_update_add_ogb_by_2_carry_out)
        self.wire(l_csa_bezout_inter.ports.u_delta_update_add_ogb_by_2_sum_out, n_csa_bezout_inter.ports.u_delta_update_add_ogb_by_2_sum_out)
        self.wire(l_csa_bezout_inter.ports.u_delta_update_sub_first_ogb_by_2_carry_out, n_csa_bezout_inter.ports.u_delta_update_sub_first_ogb_by_2_carry_out)
        self.wire(l_csa_bezout_inter.ports.u_delta_update_sub_first_ogb_by_2_sum_out, n_csa_bezout_inter.ports.u_delta_update_sub_first_ogb_by_2_sum_out)

        self.wire(u_csa_bezout_inter.ports.u_delta_update_add_even, y_csa_bezout_inter.ports.u_delta_update_add_even)
        self.wire(l_csa_bezout_inter.ports.u_delta_update_add_even, n_csa_bezout_inter.ports.u_delta_update_add_even)
        self.wire(u_csa_bezout_inter.ports.u_delta_update_sub_first_even, y_csa_bezout_inter.ports.u_delta_update_sub_first_even)
        self.wire(l_csa_bezout_inter.ports.u_delta_update_sub_first_even, n_csa_bezout_inter.ports.u_delta_update_sub_first_even)
        
        self.wire(u_csa_bezout_inter.ports.u_ogb_carry_7_out, y_csa_bezout_inter.ports.u_ogb_carry_7_out)
        self.wire(u_csa_bezout_inter.ports.u_ogb_sum_7_out, y_csa_bezout_inter.ports.u_ogb_sum_7_out)
        self.wire(u_csa_bezout_inter.ports.u_ogb_carry_8_out, y_csa_bezout_inter.ports.u_ogb_carry_8_out)
        self.wire(u_csa_bezout_inter.ports.u_ogb_sum_8_out, y_csa_bezout_inter.ports.u_ogb_sum_8_out)

        self.wire(u_csa_bezout_inter.ports.u_ogb_carry_7_by_2_out, y_csa_bezout_inter.ports.u_ogb_carry_7_by_2_out)
        self.wire(u_csa_bezout_inter.ports.u_ogb_sum_7_by_2_out, y_csa_bezout_inter.ports.u_ogb_sum_7_by_2_out)
        self.wire(u_csa_bezout_inter.ports.u_ogb_carry_8_by_2_out, y_csa_bezout_inter.ports.u_ogb_carry_8_by_2_out)
        self.wire(u_csa_bezout_inter.ports.u_ogb_sum_8_by_2_out, y_csa_bezout_inter.ports.u_ogb_sum_8_by_2_out)

        self.wire(u_csa_bezout_inter.ports.u_ogb_carry_7_ogb_by_2_out, y_csa_bezout_inter.ports.u_ogb_carry_7_ogb_by_2_out)
        self.wire(u_csa_bezout_inter.ports.u_ogb_sum_7_ogb_by_2_out, y_csa_bezout_inter.ports.u_ogb_sum_7_ogb_by_2_out)
        self.wire(u_csa_bezout_inter.ports.u_ogb_carry_8_ogb_by_2_out, y_csa_bezout_inter.ports.u_ogb_carry_8_ogb_by_2_out)
        self.wire(u_csa_bezout_inter.ports.u_ogb_sum_8_ogb_by_2_out, y_csa_bezout_inter.ports.u_ogb_sum_8_ogb_by_2_out)

        self.wire(l_csa_bezout_inter.ports.u_ogb_carry_7_out, n_csa_bezout_inter.ports.u_ogb_carry_7_out)
        self.wire(l_csa_bezout_inter.ports.u_ogb_sum_7_out, n_csa_bezout_inter.ports.u_ogb_sum_7_out)
        self.wire(l_csa_bezout_inter.ports.u_ogb_carry_8_out, n_csa_bezout_inter.ports.u_ogb_carry_8_out)
        self.wire(l_csa_bezout_inter.ports.u_ogb_sum_8_out, n_csa_bezout_inter.ports.u_ogb_sum_8_out)

        self.wire(l_csa_bezout_inter.ports.u_ogb_carry_7_by_2_out, n_csa_bezout_inter.ports.u_ogb_carry_7_by_2_out)
        self.wire(l_csa_bezout_inter.ports.u_ogb_sum_7_by_2_out, n_csa_bezout_inter.ports.u_ogb_sum_7_by_2_out)
        self.wire(l_csa_bezout_inter.ports.u_ogb_carry_8_by_2_out, n_csa_bezout_inter.ports.u_ogb_carry_8_by_2_out)
        self.wire(l_csa_bezout_inter.ports.u_ogb_sum_8_by_2_out, n_csa_bezout_inter.ports.u_ogb_sum_8_by_2_out)

        self.wire(l_csa_bezout_inter.ports.u_ogb_carry_7_ogb_by_2_out, n_csa_bezout_inter.ports.u_ogb_carry_7_ogb_by_2_out)
        self.wire(l_csa_bezout_inter.ports.u_ogb_sum_7_ogb_by_2_out, n_csa_bezout_inter.ports.u_ogb_sum_7_ogb_by_2_out)
        self.wire(l_csa_bezout_inter.ports.u_ogb_carry_8_ogb_by_2_out, n_csa_bezout_inter.ports.u_ogb_carry_8_ogb_by_2_out)
        self.wire(l_csa_bezout_inter.ports.u_ogb_sum_8_ogb_by_2_out, n_csa_bezout_inter.ports.u_ogb_sum_8_ogb_by_2_out)

        if self.final_clock_factor == 0:
            self.final_clock = self.clk
        else:
            self.final_counter = self.var("final_counter", clog2(self.final_clock_factor))
            final_clock_ = self.var("final_clock_", 1)
            self.final_clock = k.util.clock(final_clock_)
            self.wire(final_clock_, k.util.clock(self.final_counter[clog2(self.final_clock_factor) - 1]))
            self.add_code(self.set_final_counter)

        final_update = PostProcessing(self.inter_bit_length,
                                      self.bit_length,
                                      DW=self.DW)

        self.add_child("final_update",
                       final_update,
                       clk=self.final_clock,
                       rst_n=self.rst_n,
                       a_out_carry_preshift=self.a_out_carry_preshift,
                       a_out_sum_preshift=self.a_out_sum_preshift,
                       u_carry_in=self.u_carry,
                       u_sum_in=self.u_sum,
                       y_carry_in=self.y_carry,
                       y_sum_in=self.y_sum,
                       n_carry_in=self.n_carry,
                       n_sum_in=self.n_sum,
                       l_carry_in=self.l_carry,
                       l_sum_in=self.l_sum,
                       done_inter=self.done_inter,
                       even_case=self.even_case,
                       bezout_a=self.bezout_a,
                       bezout_b=self.bezout_b,
                       done_output=self.done)

        if self.debug_print:
            self.case = self.output("case_", 10)

            self.a = self.var("a", self.inter_bit_length)
            self.b = self.var("b", self.inter_bit_length)

            self.a = self.var("a", self.inter_bit_length)
            self.wire(self.a, self.a_carry + self.a_sum)
            self.b = self.var("b", self.inter_bit_length)
            self.wire(self.b, self.b_carry + self.b_sum)
            self.y = self.var("y", self.inter_bit_length)
            self.wire(self.y, self.y_carry + self.y_sum)
            self.u = self.var("u", self.inter_bit_length)
            self.wire(self.u, self.u_carry + self.u_sum)
            self.n = self.var("n", self.inter_bit_length)
            self.wire(self.n, self.n_carry + self.n_sum)
            self.l = self.var("l", self.inter_bit_length)
            self.wire(self.l, self.l_carry + self.l_sum)

            self.add_code(self.debug_case)

        termination_condition = TerminationCondition(self.bit_length, 
                                        self.inter_bit_length, 
                                        self.delta_msb,
                                        cycle_count_bit_width=self.cycle_count_bit_width,
                                        constant_time_support=self.constant_time_support)

        self.add_child("termination_condition",
                        termination_condition,
                        clk=self.final_clock,
                        rst_n=self.rst_n,
                        a_carry=self.a_carry,
                        a_sum=self.a_sum,
                        b_carry=self.b_carry,
                        b_sum=self.b_sum,
                        done=self.done_inter)

        if self.constant_time_support:
            self.wire(termination_condition.ports.constant_time, self.constant_time)
            self.wire(termination_condition.ports.total_cycle_count, self.total_cycle_count_inter)

        self.wire(self.compute, self.done_inter | self.og_cycle)

        self.add_code(self.set_internal_start)
        self.add_code(self.set_keep_start)
        self.add_code(self.set_lsbs)
        self.add_code(self.update_delta)

        # add clock enable
        if self.add_clk_en:
            self.clk_en = self.clock_en("clk_en", 1)
            k.passes.auto_insert_clock_enable(self.internal_generator)

    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def set_internal_start(self):
        if ~self.rst_n:
            self.internal_start = 0
        # elif self.gcd_clk_en:
        elif self.start | self.keep_start:
            self.internal_start = 1
        else:
            self.internal_start = 0

    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def set_keep_start(self):
        if ~self.rst_n:
            self.keep_start = 0
        elif self.start:
            self.keep_start = 1
        else:
            self.keep_start = 0

    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def set_lsbs(self):
        if ~self.rst_n:
            self.uupdated_u_y_after_lsb = 0
            self.lupdated_u_y_after_lsb = 0
            self.uupdated_u_y_after_lsb_sub = 0
            self.lupdated_u_y_after_lsb_sub = 0

            self.uupdated_u_y_after_lsb_2 = 0
            self.lupdated_u_y_after_lsb_2 = 0
            self.uupdated_u_y_after_lsb_2_sub = 0
            self.lupdated_u_y_after_lsb_2_sub = 0

            self.uupdated_inv_u_y_ogb_after_lsb_2 = 0
            self.lupdated_inv_u_y_ogb_after_lsb_2 = 0

            self.uupdated_inv_u_y_ogb_after_lsb_2_sub = 0
            self.lupdated_inv_u_y_ogb_after_lsb_2_sub = 0

        elif self.internal_start:
            self.uupdated_u_y_after_lsb = 1
            self.lupdated_u_y_after_lsb = 1
            self.uupdated_u_y_after_lsb_sub = 1
            self.lupdated_u_y_after_lsb_sub = 1

            # won't be divisible by 4 since it's not divisble by 2,
            # so it doesn't really matter what we set these
            self.uupdated_u_y_after_lsb_2 = 1
            self.lupdated_u_y_after_lsb_2 = 1
            self.uupdated_u_y_after_lsb_2_sub = 1
            self.lupdated_u_y_after_lsb_2_sub = 1

            self.uupdated_inv_u_y_ogb_after_lsb_2 = self.og_b_div4
            self.lupdated_inv_u_y_ogb_after_lsb_2 = self.og_a_div4

            # u - y = u + y = 1, so this is just 1 + og_b and same as
            # uupdated_inv_u_y_ogb_after_lsb_2
            self.uupdated_inv_u_y_ogb_after_lsb_2_sub = self.og_b_div4
            # l - n = -1, so we need lsb 2 for -1 - a which is same as
            # lsb 2 for 1 + a (negative of the number we are looking for)
            self.lupdated_inv_u_y_ogb_after_lsb_2_sub = self.og_a_div4_plus

        elif ~(self.compute):
            if self.update_a:
                self.uupdated_u_y_after_lsb = self.uu_y_after_lsb
                self.lupdated_u_y_after_lsb = self.lu_y_after_lsb
                self.uupdated_u_y_after_lsb_sub = self.uu_y_after_lsb_sub
                self.lupdated_u_y_after_lsb_sub = self.lu_y_after_lsb_sub

                self.uupdated_u_y_after_lsb_2 = self.uu_y_after_lsb_2
                self.lupdated_u_y_after_lsb_2 = self.lu_y_after_lsb_2
                self.uupdated_u_y_after_lsb_2_sub = self.uu_y_after_lsb_2_sub
                self.lupdated_u_y_after_lsb_2_sub = self.lu_y_after_lsb_2_sub

                self.uupdated_inv_u_y_ogb_after_lsb_2 = self.uinv_u_y_ogb_after_lsb_2
                self.lupdated_inv_u_y_ogb_after_lsb_2 = self.linv_u_y_ogb_after_lsb_2
                
                # u - y
                self.uupdated_inv_u_y_ogb_after_lsb_2_sub = self.uinv_u_y_ogb_after_lsb_2_sub
                # l - n
                self.lupdated_inv_u_y_ogb_after_lsb_2_sub = self.linv_u_y_ogb_after_lsb_2_sub

            else:
                self.uupdated_u_y_after_lsb = self.yu_y_after_lsb
                self.lupdated_u_y_after_lsb = self.nu_y_after_lsb
                self.uupdated_u_y_after_lsb_sub = self.yu_y_after_lsb_sub
                self.lupdated_u_y_after_lsb_sub = self.nu_y_after_lsb_sub

                self.uupdated_u_y_after_lsb_2 = self.yu_y_after_lsb_2
                self.lupdated_u_y_after_lsb_2 = self.nu_y_after_lsb_2
                self.uupdated_u_y_after_lsb_2_sub = ~self.yu_y_after_lsb_2_sub
                self.lupdated_u_y_after_lsb_2_sub = ~self.nu_y_after_lsb_2_sub

                self.uupdated_inv_u_y_ogb_after_lsb_2 = self.yinv_u_y_ogb_after_lsb_2
                self.lupdated_inv_u_y_ogb_after_lsb_2 = self.ninv_u_y_ogb_after_lsb_2

                # y - u, but need to set u - y, so we use switch signals in Update_Bezout
                self.uupdated_inv_u_y_ogb_after_lsb_2_sub = self.yinv_u_y_ogb_after_lsb_2_sub
                self.lupdated_inv_u_y_ogb_after_lsb_2_sub = self.ninv_u_y_ogb_after_lsb_2_sub

    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def set_total_cycle_count_inter(self):
        if ~self.rst_n:
            self.total_cycle_count_inter = 0
        elif self.internal_start:
            self.total_cycle_count_inter = 0
        elif ~self.done:
            self.total_cycle_count_inter = self.total_cycle_count_inter + 1
    
    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def set_final_counter(self):
        if ~self.rst_n:
            self.final_counter = 0
        elif self.internal_start:
            self.final_counter = self.final_clock_factor - 1
        else:
            self.final_counter = self.final_counter + 1

    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def set_start_counter(self):
        if ~self.rst_n:
            self.start_counter = 0
        elif self.start:
            self.start_counter = self.start_clock_factor - 1
        else:
            self.start_counter = self.start_counter + 1
                
    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def update_delta(self):
        if ~self.rst_n:
            self.delta = 0
        elif self.internal_start:
            self.delta = 0
        elif ~(self.compute):
            if self.shift_a_8 & ~self.a_after_lsb_3 & ~self.a_after_lsb_2 & ~self.a_after_lsb:
                self.delta = self.delta - 3
            elif self.shift_a_4 & ~self.a_after_lsb_2 & ~self.a_after_lsb:
                self.delta = self.delta - 2
            elif ~self.a_after_lsb:
                self.delta = self.delta - 1
            elif self.shift_b_8 & ~self.b_after_lsb_3 & ~self.b_after_lsb_2 & ~self.b_after_lsb:
                self.delta = self.delta + 3
            elif self.shift_b_4 & ~self.b_after_lsb_2 & ~self.b_after_lsb:
                self.delta = self.delta + 2
            elif ~self.b_after_lsb:
                self.delta = self.delta + 1
            elif self.shift_b_2_odd:
                self.delta = self.delta
            elif unsigned(~self.delta[self.delta_msb]):
                if self.ab_after_lsb_2:
                    if self.shift_b_8_odd & self.ab_after_lsb_3:
                        self.delta = self.delta - 2
                    else:
                        self.delta = self.delta - 1
                else:
                    if self.shift_b_8_odd & self.a_minus_b_after_lsb_3:
                        self.delta = self.delta - 2
                    else:
                        self.delta = self.delta - 1
            elif ~unsigned(~self.delta[self.delta_msb]) & self.ab_after_lsb_2:
                if self.shift_b_8_odd & self.ab_after_lsb_3:
                    self.delta = self.delta + 2
                else:
                    self.delta = self.delta + 1
            elif ~unsigned(~self.delta[self.delta_msb]):
                if self.shift_b_8_odd & self.a_minus_b_after_lsb_3:
                    self.delta = self.delta + 2
                else:
                    self.delta = self.delta + 1

    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def debug_case(self):
        if ~self.rst_n:
            self.case = 0
        elif ~(self.compute):
            if self.shift_a_8 & ~self.a_after_lsb_3 & ~self.a_after_lsb_2 & ~self.a_after_lsb:
                self.case = 9
            elif self.shift_a_4 & ~self.a_after_lsb_2 & ~self.a_after_lsb:
                self.case = 1
            elif ~self.a_after_lsb:
                self.case = 2
            elif self.shift_b_8 & ~self.b_after_lsb_3 & ~self.b_after_lsb_2 & ~self.b_after_lsb:
                self.case = 10
            elif self.shift_b_4 & ~self.b_after_lsb_2 & ~self.b_after_lsb:
                self.case = 3
            elif ~self.b_after_lsb:
                self.case = 4
            # this always block is added only for debugging purposes, so it is okay to
            # use mods (inefficient logic) here
            elif unsigned(~self.delta[self.delta_msb]):
                if self.shift_b_2_odd:
                    self.case = 11
                elif self.ab_after_lsb_2:
                    if self.shift_b_8_odd & self.ab_after_lsb_3:
                        self.case = 16
                    else:
                        self.case = 5
                else:
                    if self.shift_b_8_odd & self.a_minus_b_after_lsb_3:
                        self.case = 18
                    else:
                        self.case = 6
            # this always block is added only for debugging purposes, so it is okay to
            # use mods (inefficient logic) here
            elif self.shift_b_2_odd:
                self.case = 12
            elif ~unsigned(~self.delta[self.delta_msb]) & self.ab_after_lsb_2:
                if self.shift_b_8_odd & self.ab_after_lsb_3:
                    self.case = 20
                else:
                    self.case = 7
            elif ~unsigned(~self.delta[self.delta_msb]):
                if self.shift_b_8_odd & self.a_minus_b_after_lsb_3:
                    self.case = 22
                else:
                    self.case = 8


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Extended GCD hardware generator")
    parser.add_argument('--bit_length', type=int, default=1024, help="bitwidth for XGCD")
    parser.add_argument('--constant_time_support', default=False, action="store_true", help="(default: False) constant-time XGCD (worst-case number of iterations)")
    parser.add_argument('--reduction_factor_even', type=int, default=8, help="Factor of 2 to reduce b by each cycle if even")
    parser.add_argument('--reduction_factor_odd', type=int, default=4, help="Factor of 2 to reduce b when odd by each cycle if even")
    parser.add_argument('--csa_handwritten', default=False, action="store_true", help="(default: False) if used, use CSA handwritten module instead of DesignWare CSA module")
    parser.add_argument('--output', default="XGCDTop.v", help="name of output Verilog file")
    args = parser.parse_args()

    print("Verilog Generation Parameter Summary: ")
    print(args)

    dut = XGCDTop(bit_length=args.bit_length,
                  final_clock_factor=4,
                  start_clock_factor=2,
                  shift_factor_a=args.reduction_factor_even,
                  shift_factor_b=args.reduction_factor_even,
                  shift_factor_b_odd=args.reduction_factor_odd,
                  constant_time_support=args.constant_time_support,
                  DW=(not args.csa_handwritten))

    verilog(dut, filename=args.output)

    print()
    print(f"Generated Verilog is at {args.output}")

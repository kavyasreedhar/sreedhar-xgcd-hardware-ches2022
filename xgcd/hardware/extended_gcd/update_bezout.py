import kratos
from kratos import *

from xgcd.hardware.csa import *
from xgcd.hardware.extended_gcd.update_bezout_odd import *


class Update_Bezout(Generator):
    def __init__(self,
                 inter_bit_length,
                 add_og_val,
                 initial_0,
                 u_l,
                 u_y,
                 testing=False,
                 DW=True,
                 debug_print=False):
        super().__init__(f"Update_Bezout_{inter_bit_length}", debug=True)

        # Notes:
        # - set_u code block comments on what the various signals are used for
        # - all code blocks follow the same structure as set_u
        # - control signals are duplicated and computed in parallel for each case
        # for late selects

        # parameters
        self.inter_bit_length = inter_bit_length
        self.add_og_val = add_og_val
        self.initial_0 = initial_0
        self.u_l = u_l
        self.u_y = u_y
        self.DW = DW
        self.debug_print = debug_print
        
        self.clk = self.clock("clk")
        self.rst_n = self.reset("rst_n", 1)
        self.start = self.input("start", 1)
        self.done = self.input("done", 1)

        # related Bezout coefficient value
        self.y_carry_in = self.input("y_carry_in", self.inter_bit_length)
        self.y_sum_in = self.input("y_sum_in", self.inter_bit_length)

        # Bezout coefficient input and update (output)
        self.u_carry = self.var("u_carry", self.inter_bit_length)
        self.u_sum = self.var("u_sum", self.inter_bit_length)
        self.u_carry_out = self.output("u_carry_out", self.inter_bit_length)
        self.u_sum_out = self.output("u_sum_out", self.inter_bit_length)
        self.wire(self.u_carry_out, self.u_carry)
        self.wire(self.u_sum_out, self.u_sum)

        self.delta_sign = self.input("delta_sign", 1)

        # divisibility of a, b
        self.a_lsb = self.input("a_lsb", 1)
        self.a_lsb_2 = self.input("a_lsb_2", 1)
        self.a_lsb_3 = self.input("a_lsb_3", 1)
        self.b_lsb = self.input("b_lsb", 1)
        
        self.a_plus_b_4 = self.input("a_plus_b_4", 1)
        self.a_plus_b_8 = self.input("a_plus_b_8", 1)
        self.a_minus_b_8 = self.input("a_minus_b_8", 1)

        # reduction factor signals
        self.shift_a_4 = self.input("shift_a_4", 1)
        self.shift_a_8 = self.input("shift_a_8", 1)
        self.shift_b_2_odd = self.input("shift_b_2_odd", 1)
        self.shift_b_8_odd = self.input("shift_b_8_odd", 1)

        # constant signals
        self.og_b = self.input("og_b", self.inter_bit_length)
        self.og_b2 = self.input("og_b2", self.inter_bit_length)
        self.og_b3 = self.input("og_b3", self.inter_bit_length)
        self.og_b4 = self.input("og_b4", self.inter_bit_length)
        self.og_b5 = self.input("og_b5", self.inter_bit_length)
        self.og_b6 = self.input("og_b6", self.inter_bit_length)
        self.og_b7 = self.input("og_b7", self.inter_bit_length)

        # divisibility signals (control signals)
        self.u_y_after_lsb = self.output("u_y_after_lsb", 1)
        self.u_y_after_lsb_sub = self.output("u_y_after_lsb_sub", 1)
        self.updated_u_y_after_lsb = self.input("updated_u_y_after_lsb", 1)
        self.updated_u_y_after_lsb_sub = self.input("updated_u_y_after_lsb_sub", 1)

        self.u_y_after_lsb_2 = self.output("u_y_after_lsb_2", 1)
        self.u_y_after_lsb_2_sub = self.output("u_y_after_lsb_2_sub", 1)
        self.updated_u_y_after_lsb_2 = self.input("updated_u_y_after_lsb_2", 1)
        self.updated_u_y_after_lsb_2_sub = self.input("updated_u_y_after_lsb_2_sub", 1)

        self.inv_u_y_ogb_after_lsb_2 = self.output("inv_u_y_ogb_after_lsb_2", 1)
        self.updated_inv_u_y_ogb_after_lsb_2 = self.input("updated_inv_u_y_ogb_after_lsb_2", 1)
        self.inv_u_y_ogb_after_lsb_2_sub = self.output("inv_u_y_ogb_after_lsb_2_sub", 1)
        self.updated_inv_u_y_ogb_after_lsb_2_sub = self.input("updated_inv_u_y_ogb_after_lsb_2_sub", 1)
        self.inv_u_y_ogb_after_lsb_2_sub_switch = self.output("inv_u_y_ogb_after_lsb_2_sub_switch", 1)

        self.ci = self.var("ci", 1)
        self.og_b_csa = self.var("og_b_csa", self.inter_bit_length)
        self.og_b2_csa = self.var("og_b2_csa", self.inter_bit_length)
        self.og_b3_csa = self.var("og_b3_csa", self.inter_bit_length)
        self.og_b4_csa = self.var("og_b4_csa", self.inter_bit_length)
        self.og_b5_csa = self.var("og_b5_csa", self.inter_bit_length)
        self.og_b6_csa = self.var("og_b6_csa", self.inter_bit_length)
        self.og_b7_csa = self.var("og_b7_csa", self.inter_bit_length)

        if self.add_og_val:
            self.wire(self.ci, const(0, 1))
            self.wire(self.og_b_csa, self.og_b)
            self.wire(self.og_b2_csa, self.og_b2)
            self.wire(self.og_b3_csa, self.og_b3)
            self.wire(self.og_b4_csa, self.og_b4)
            self.wire(self.og_b5_csa, self.og_b5)
            self.wire(self.og_b6_csa, self.og_b6)
            self.wire(self.og_b7_csa, self.og_b7)
        else:
            self.wire(self.ci, const(1, 1))
            self.wire(self.og_b_csa, ~self.og_b)
            self.wire(self.og_b2_csa, ~self.og_b2)
            self.wire(self.og_b3_csa, ~self.og_b3)
            self.wire(self.og_b4_csa, ~self.og_b4)
            self.wire(self.og_b5_csa, ~self.og_b5)
            self.wire(self.og_b6_csa, ~self.og_b6)
            self.wire(self.og_b7_csa, ~self.og_b7)

        if self.u_l:
            self.u_delta_update_add_carry = self.var("u_delta_update_add_carry", self.inter_bit_length)
            self.u_delta_update_add_sum = self.var("u_delta_update_add_sum", self.inter_bit_length)
            self.u_delta_update_add_carry_by_2 = self.var("u_delta_update_add_carry_by_2", self.inter_bit_length)
            self.u_delta_update_add_sum_by_2 = self.var("u_delta_update_add_sum_by_2", self.inter_bit_length)
            self.u_delta_update_add_ogb_by_2_carry = self.var("u_delta_update_add_ogb_by_2_carry", self.inter_bit_length)
            self.u_delta_update_add_ogb_by_2_sum = self.var("u_delta_update_add_ogb_by_2_sum", self.inter_bit_length)

            self.u_delta_update_sub_first_carry = self.var("u_delta_update_sub_first_carry", self.inter_bit_length)
            self.u_delta_update_sub_first_sum = self.var("u_delta_update_sub_first_sum", self.inter_bit_length)
            self.u_delta_update_sub_first_carry_by_2 = self.var("u_delta_update_sub_first_carry_by_2", self.inter_bit_length)
            self.u_delta_update_sub_first_sum_by_2 = self.var("u_delta_update_sub_first_sum_by_2", self.inter_bit_length)
            self.u_delta_update_sub_first_ogb_by_2_carry = self.var("u_delta_update_sub_first_ogb_by_2_carry", self.inter_bit_length)
            self.u_delta_update_sub_first_ogb_by_2_sum = self.var("u_delta_update_sub_first_ogb_by_2_sum", self.inter_bit_length)

            self.u_delta_update_add_even = self.output("u_delta_update_add_even", 1)
            self.wire(self.u_delta_update_add_even, ~(self.u_delta_update_add_carry[0] ^ self.u_delta_update_add_sum[0]))

            self.u_delta_update_sub_first_even = self.output("u_delta_update_sub_first_even", 1)
            self.wire(self.u_delta_update_sub_first_even, ~(self.u_delta_update_sub_first_carry[0] ^ self.u_delta_update_sub_first_sum[0]))

            u_odd_delta_update_add = UpdateBezoutOdd(self.inter_bit_length,
                                                       False,
                                                       False,
                                                       self.add_og_val,
                                                       testing=testing,
                                                       DW=self.DW,
                                                       debug_print=self.debug_print)
            self.add_child("u_odd_delta_update_add",
                        u_odd_delta_update_add,
                        og_b=self.og_b,
                        og_b2=self.og_b2,
                        og_b3=self.og_b3,
                        shift_b_2_odd=self.shift_b_2_odd,
                        u_y_after_lsb=self.updated_u_y_after_lsb,
                        u_y_after_lsb_2=self.updated_u_y_after_lsb_2,
                        inv_u_y_ogb_lsb_2_after=self.updated_inv_u_y_ogb_after_lsb_2,
                        u_carry_in=self.u_carry,
                        u_sum_in=self.u_sum,
                        y_carry_in=self.y_carry_in,
                        y_sum_in=self.y_sum_in,
                        u_carry=self.u_delta_update_add_carry,
                        u_sum=self.u_delta_update_add_sum)

            self.u_delta_update_add_carry_by_2 = self.var("u_delta_update_add_carry_by_2", self.inter_bit_length)
            self.u_delta_update_add_sum_by_2 = self.var("u_delta_update_add_sum_by_2", self.inter_bit_length)

            shiftu_delta_update_add_carry = DW01_csa_shift_only(self.inter_bit_length)
            self.add_child("shiftu_delta_update_add_carry",
                        shiftu_delta_update_add_carry,
                        final_out_carry=self.u_delta_update_add_carry,
                        final_out_sum=self.u_delta_update_add_sum,
                        shifted_out_carry=self.u_delta_update_add_carry_by_2,
                        shifted_out_sum=self.u_delta_update_add_sum_by_2)
            
            # u_delta_update_add + og_b
            self.u_delta_update_add_ogb_carry = self.var("u_delta_update_add_ogb_carry", self.inter_bit_length)
            self.u_delta_update_add_ogb_sum = self.var("u_delta_update_add_ogb_sum", self.inter_bit_length)

            csa_u_delta_update_add_ogb = DW01_csa(self.inter_bit_length, DW=self.DW)
            csa_u_delta_update_add_ogb.width.value = self.inter_bit_length
            self.add_child("csa_u_delta_update_add_ogb", 
                        csa_u_delta_update_add_ogb,
                        a=self.u_delta_update_add_carry,
                        b=self.u_delta_update_add_sum,
                        c=self.og_b_csa,
                        ci=self.ci,
                        carry=self.u_delta_update_add_ogb_carry,
                        sum=self.u_delta_update_add_ogb_sum)

            # (u_delta_update_add + og_b) // 2
            self.u_delta_update_add_ogb_by_2_carry = self.var("u_delta_update_add_ogb_by_2_carry", self.inter_bit_length)
            self.u_delta_update_add_ogb_by_2_sum = self.var("u_delta_update_add_ogb_by_2_sum", self.inter_bit_length)

            shiftu_delta_update_add_ogb = DW01_csa_shift_only(self.inter_bit_length)
            self.add_child("shiftu_delta_update_add_ogb",
                        shiftu_delta_update_add_ogb,
                        final_out_carry=self.u_delta_update_add_ogb_carry,
                        final_out_sum=self.u_delta_update_add_ogb_sum,
                        shifted_out_carry=self.u_delta_update_add_ogb_by_2_carry,
                        shifted_out_sum=self.u_delta_update_add_ogb_by_2_sum)

            u_odd_delta_update_sub = UpdateBezoutOdd(self.inter_bit_length,
                                                       True,
                                                       self.u_l,
                                                       self.add_og_val,
                                                       testing=testing,
                                                       DW=self.DW,
                                                       debug_print=self.debug_print)
            self.add_child("u_odd_delta_update_sub",
                        u_odd_delta_update_sub,
                        og_b=self.og_b,
                        og_b2=self.og_b2,
                        og_b3=self.og_b3,
                        shift_b_2_odd=self.shift_b_2_odd,
                        u_y_after_lsb=self.updated_u_y_after_lsb_sub,
                        u_y_after_lsb_2=self.updated_u_y_after_lsb_2_sub,
                        inv_u_y_ogb_lsb_2_after=self.updated_inv_u_y_ogb_after_lsb_2_sub,
                        u_carry_in=self.u_carry,
                        u_sum_in=self.u_sum,
                        y_carry_in=self.y_carry_in,
                        y_sum_in=self.y_sum_in,
                        u_carry=self.u_delta_update_sub_first_carry,
                        u_sum=self.u_delta_update_sub_first_sum)

            self.u_delta_update_sub_first_carry_by_2 = self.var("u_delta_update_sub_first_carry_by_2", self.inter_bit_length)
            self.u_delta_update_sub_first_sum_by_2 = self.var("u_delta_update_sub_first_sum_by_2", self.inter_bit_length)

            shiftu_delta_update_sub_first_carry = DW01_csa_shift_only(self.inter_bit_length)
            self.add_child("shiftu_delta_update_sub_first_carry",
                        shiftu_delta_update_sub_first_carry,
                        final_out_carry=self.u_delta_update_sub_first_carry,
                        final_out_sum=self.u_delta_update_sub_first_sum,
                        shifted_out_carry=self.u_delta_update_sub_first_carry_by_2,
                        shifted_out_sum=self.u_delta_update_sub_first_sum_by_2)
            
            # u_delta_update_add + og_b
            self.u_delta_update_sub_first_ogb_carry = self.var("u_delta_update_sub_first_ogb_carry", self.inter_bit_length)
            self.u_delta_update_sub_first_ogb_sum = self.var("u_delta_update_sub_first_ogb_sum", self.inter_bit_length)

            csa_u_delta_update_sub_first_ogb = DW01_csa(self.inter_bit_length, DW=self.DW)
            csa_u_delta_update_sub_first_ogb.width.value = self.inter_bit_length
            self.add_child("csa_u_delta_update_sub_first_ogb", 
                        csa_u_delta_update_sub_first_ogb,
                        a=self.u_delta_update_sub_first_carry,
                        b=self.u_delta_update_sub_first_sum,
                        c=self.og_b_csa,
                        ci=self.ci,
                        carry=self.u_delta_update_sub_first_ogb_carry,
                        sum=self.u_delta_update_sub_first_ogb_sum)
            
            # (u_delta_update_add + og_b) // 2
            self.u_delta_update_sub_first_ogb_by_2_carry = self.var("u_delta_update_sub_first_ogb_by_2_carry", self.inter_bit_length)
            self.u_delta_update_sub_first_ogb_by_2_sum = self.var("u_delta_update_sub_first_ogb_by_2_sum", self.inter_bit_length)

            shiftu_delta_update_sub_first_ogb = DW01_csa_shift_only(self.inter_bit_length)
            self.add_child("shiftu_delta_update_sub_first_ogb",
                        shiftu_delta_update_sub_first_ogb,
                        final_out_carry=self.u_delta_update_sub_first_ogb_carry,
                        final_out_sum=self.u_delta_update_sub_first_ogb_sum,
                        shifted_out_carry=self.u_delta_update_sub_first_ogb_by_2_carry,
                        shifted_out_sum=self.u_delta_update_sub_first_ogb_by_2_sum)

        # u // 2
        self.u_carry_by_2 = self.var("u_carry_by_2", self.inter_bit_length)
        self.u_sum_by_2 = self.var("u_sum_by_2", self.inter_bit_length)

        shiftu = DW01_csa_shift_only(self.inter_bit_length)
        self.add_child("shiftu",
                       shiftu,
                       final_out_carry=self.u_carry,
                       final_out_sum=self.u_sum,
                       shifted_out_carry=self.u_carry_by_2,
                       shifted_out_sum=self.u_sum_by_2)

        # u // 4
        self.u_carry_by_4 = self.var("u_carry_by_4", self.inter_bit_length)
        self.u_sum_by_4 = self.var("u_sum_by_4", self.inter_bit_length)

        shiftu4 = DW01_csa_shift_only_4(self.inter_bit_length)
        self.add_child("shiftu4",
                       shiftu4,
                       final_out_carry=self.u_carry,
                       final_out_sum=self.u_sum,
                       shifted_out_carry=self.u_carry_by_4,
                       shifted_out_sum=self.u_sum_by_4)

        # (u // 2 + og_b) // 2 = (u + 2 * og_b) // 4
        self.u_ogb2_carry = self.var("u_ogb2_carry", self.inter_bit_length)
        self.u_ogb2_sum = self.var("u_ogb2_sum", self.inter_bit_length)

        csa_u_ogb2 = DW01_csa(self.inter_bit_length, DW=self.DW)
        csa_u_ogb2.width.value = self.inter_bit_length
        self.add_child("csa_u_ogb2", 
                       csa_u_ogb2,
                       a=self.u_carry,
                       b=self.u_sum,
                       c=self.og_b2_csa,
                       ci=self.ci,
                       carry=self.u_ogb2_carry,
                       sum=self.u_ogb2_sum)
        
        self.u_ogb2_by4_carry = self.var("u_ogb2_by4_carry", self.inter_bit_length)
        self.u_ogb2_by4_sum = self.var("u_ogb2_by4_sum", self.inter_bit_length)

        shiftu_ogb2_by4 = DW01_csa_shift_only_4(self.inter_bit_length)
        self.add_child("shiftu_ogb2_by4",
                       shiftu_ogb2_by4,
                       final_out_carry=self.u_ogb2_carry,
                       final_out_sum=self.u_ogb2_sum,
                       shifted_out_carry=self.u_ogb2_by4_carry,
                       shifted_out_sum=self.u_ogb2_by4_sum)

        # u + og_b
        self.u_ogb_carry = self.var("u_ogb_carry", self.inter_bit_length)
        self.u_ogb_sum = self.var("u_ogb_sum", self.inter_bit_length)

        csa_u_ogb = DW01_csa(self.inter_bit_length, DW=self.DW)
        csa_u_ogb.width.value = self.inter_bit_length
        self.add_child("csa_u_ogb", 
                       csa_u_ogb,
                       a=self.u_carry,
                       b=self.u_sum,
                       c=self.og_b_csa,
                       ci=self.ci,
                       carry=self.u_ogb_carry,
                       sum=self.u_ogb_sum)
        
        if self.u_y:
            self.u_after_lsb = self.var("u_after_lsb", 1)
            self.u_after_lsb_2 = self.var("u_after_lsb_2", 1)
            self.u_after_lsb_3 = self.var("u_after_lsb_3", 1)

            self.u_after_lsb_out = self.output("u_after_lsb_out", 1)
            self.u_after_lsb_2_out = self.output("u_after_lsb_2_out", 1)
            self.u_after_lsb_3_out = self.output("u_after_lsb_3_out", 1)

            self.wire(self.u_after_lsb_out, self.u_after_lsb)
            self.wire(self.u_after_lsb_2_out, self.u_after_lsb_2)
            self.wire(self.u_after_lsb_3_out, self.u_after_lsb_3)

        else:
            self.u_after_lsb = self.input("u_after_lsb", 1)
            self.u_after_lsb_2 = self.input("u_after_lsb_2", 1)
            self.u_after_lsb_3 = self.input("u_after_lsb_3", 1)
        
        # (u + og_b) // 2
        self.u_ogb_by_2_carry = self.var("u_ogb_by_2_carry", self.inter_bit_length)
        self.u_ogb_by_2_sum = self.var("u_ogb_by_2_sum", self.inter_bit_length)

        shiftu_ogb = DW01_csa_shift_only(self.inter_bit_length)
        self.add_child("shiftu_ogb",
                       shiftu_ogb,
                       final_out_carry=self.u_ogb_carry,
                       final_out_sum=self.u_ogb_sum,
                       shifted_out_carry=self.u_ogb_by_2_carry,
                       shifted_out_sum=self.u_ogb_by_2_sum)

        # (u + og_b) // 4
        self.u_ogb_by4_carry = self.var("u_ogb_by4_carry", self.inter_bit_length)
        self.u_ogb_by4_sum = self.var("u_ogb_by4_sum", self.inter_bit_length)

        shiftu_ogb_by4 = DW01_csa_shift_only_4(self.inter_bit_length)
        self.add_child("shiftu_ogb_by4",
                       shiftu_ogb_by4,
                       final_out_carry=self.u_ogb_carry,
                       final_out_sum=self.u_ogb_sum,
                       shifted_out_carry=self.u_ogb_by4_carry,
                       shifted_out_sum=self.u_ogb_by4_sum)

        # ((u + og_b) // 2 + og_b) // 2 = (u + 3 * og_b) // 4
        self.u_ogb3_carry = self.var("u_ogb3_carry", self.inter_bit_length)
        self.u_ogb3_sum = self.var("u_ogb3_sum", self.inter_bit_length)

        csa_u_ogb3 = DW01_csa(self.inter_bit_length, DW=self.DW)
        csa_u_ogb3.width.value = self.inter_bit_length
        self.add_child("csa_u_ogb3", 
                       csa_u_ogb3,
                       a=self.u_carry,
                       b=self.u_sum,
                       c=self.og_b3_csa,
                       ci=self.ci,
                       carry=self.u_ogb3_carry,
                       sum=self.u_ogb3_sum)

        self.u_ogb3_by4_carry = self.var("u_ogb3_by4_carry", self.inter_bit_length)
        self.u_ogb3_by4_sum = self.var("u_ogb3_by4_sum", self.inter_bit_length)

        shiftu_ogb3_by4 = DW01_csa_shift_only_4(self.inter_bit_length)
        self.add_child("shiftu_ogb3_by4",
                       shiftu_ogb3_by4,
                       final_out_carry=self.u_ogb3_carry,
                       final_out_sum=self.u_ogb3_sum,
                       shifted_out_carry=self.u_ogb3_by4_carry,
                       shifted_out_sum=self.u_ogb3_by4_sum)

        # divby8 u options

        # u // 8
        self.u_carry_by_8 = self.var("u_carry_by_8", self.inter_bit_length)
        self.u_sum_by_8 = self.var("u_sum_by_8", self.inter_bit_length)

        shiftu8 = DW01_csa_shift_only_8(bit_length=self.inter_bit_length, debug_print=self.debug_print)
        self.add_child("shiftu8",
                       shiftu8,
                       final_out_carry=self.u_carry,
                       final_out_sum=self.u_sum,
                       shifted_out_carry=self.u_carry_by_8,
                       shifted_out_sum=self.u_sum_by_8)
        
        # (i // 4 + j) // 2 = (i + 4 * j) // 8
        self.u_ogb4_carry = self.var("u_ogb4_carry", self.inter_bit_length)
        self.u_ogb4_sum = self.var("u_ogb4_sum", self.inter_bit_length)

        csa_u_ogb4 = DW01_csa(self.inter_bit_length, DW=self.DW)
        csa_u_ogb4.width.value = self.inter_bit_length
        self.add_child("csa_u_ogb4", 
                       csa_u_ogb4,
                       a=self.u_carry,
                       b=self.u_sum,
                       c=self.og_b4_csa,
                       ci=self.ci,
                       carry=self.u_ogb4_carry,
                       sum=self.u_ogb4_sum)
        
        self.u_ogb4_by_8_carry = self.var("u_ogb4_by_8_carry", self.inter_bit_length)
        self.u_ogb4_by_8_sum = self.var("u_ogb4_by_8_sum", self.inter_bit_length)

        shiftu_ogb4_by8 = DW01_csa_shift_only_8(bit_length=self.inter_bit_length, debug_print=self.debug_print)
        self.add_child("shiftu_ogb4_by8",
                       shiftu_ogb4_by8,
                       final_out_carry=self.u_ogb4_carry,
                       final_out_sum=self.u_ogb4_sum,
                       shifted_out_carry=self.u_ogb4_by_8_carry,
                       shifted_out_sum=self.u_ogb4_by_8_sum)
        
        # (u // 2 + og_b) // 4 = (u + 2 * og_b) // 8
        # u_ogb2_carry and u_ogb2_sum already computed for a divby4 case (csa_u_ogb2)
        self.u_ogb2_by8_carry = self.var("u_ogb2_by8_carry", self.inter_bit_length)
        self.u_ogb2_by8_sum = self.var("u_ogb2_by8_sum", self.inter_bit_length)

        shiftu_ogb2_by8 = DW01_csa_shift_only_8(bit_length=self.inter_bit_length, debug_print=self.debug_print)
        self.add_child("shiftu_ogb2_by8",
                       shiftu_ogb2_by8,
                       final_out_carry=self.u_ogb2_carry,
                       final_out_sum=self.u_ogb2_sum,
                       shifted_out_carry=self.u_ogb2_by8_carry,
                       shifted_out_sum=self.u_ogb2_by8_sum)
        
        # ((u // 2 + og_b) // 2 + og_b) // 2 = (u + 6 * og_b) // 8
        self.u_ogb6_carry = self.var("u_ogb6_carry", self.inter_bit_length)
        self.u_ogb6_sum = self.var("u_ogb6_sum", self.inter_bit_length)

        csa_u_ogb6 = DW01_csa(self.inter_bit_length, DW=self.DW)
        csa_u_ogb6.width.value = self.inter_bit_length
        self.add_child("csa_u_ogb6", 
                       csa_u_ogb6,
                       a=self.u_carry,
                       b=self.u_sum,
                       c=self.og_b6_csa,
                       ci=self.ci,
                       carry=self.u_ogb6_carry,
                       sum=self.u_ogb6_sum)

        self.u_ogb6_by8_carry = self.var("u_ogb6_by8_carry", self.inter_bit_length)
        self.u_ogb6_by8_sum = self.var("u_ogb6_by8_sum", self.inter_bit_length)

        shiftu_ogb6_by8 = DW01_csa_shift_only_8(bit_length=self.inter_bit_length, debug_print=self.debug_print)
        self.add_child("shiftu_ogb6_by8",
                       shiftu_ogb6_by8,
                       final_out_carry=self.u_ogb6_carry,
                       final_out_sum=self.u_ogb6_sum,
                       shifted_out_carry=self.u_ogb6_by8_carry,
                       shifted_out_sum=self.u_ogb6_by8_sum)

        # (u + og_b) // 8
        self.u_ogb_by8_carry = self.var("u_ogb_by8_carry", self.inter_bit_length)
        self.u_ogb_by8_sum = self.var("u_ogb_by8_sum", self.inter_bit_length)
        
        shiftu_ogb_by8 = DW01_csa_shift_only_8(bit_length=self.inter_bit_length, debug_print=self.debug_print)
        self.add_child("shiftu_ogb_by8",
                       shiftu_ogb_by8,
                       final_out_carry=self.u_ogb_carry,
                       final_out_sum=self.u_ogb_sum,
                       shifted_out_carry=self.u_ogb_by8_carry,
                       shifted_out_sum=self.u_ogb_by8_sum)

        # ((u + og_b) // 4 + og_b) // 2 = (u + 5 * og_b) // 8
        self.u_ogb5_carry = self.var("u_ogb5_carry", self.inter_bit_length)
        self.u_ogb5_sum = self.var("u_ogb5_sum", self.inter_bit_length)

        csa_u_ogb5 = DW01_csa(self.inter_bit_length, DW=self.DW)
        csa_u_ogb5.width.value = self.inter_bit_length
        self.add_child("csa_u_ogb5", 
                       csa_u_ogb5,
                       a=self.u_carry,
                       b=self.u_sum,
                       c=self.og_b5_csa,
                       ci=self.ci,
                       carry=self.u_ogb5_carry,
                       sum=self.u_ogb5_sum)

        self.u_ogb5_by8_carry = self.var("u_ogb5_by8_carry", self.inter_bit_length)
        self.u_ogb5_by8_sum = self.var("u_ogb5_by8_sum", self.inter_bit_length)

        shiftu_ogb5_by8 = DW01_csa_shift_only_8(bit_length=self.inter_bit_length, debug_print=self.debug_print)
        self.add_child("shiftu_ogb5_by8",
                       shiftu_ogb5_by8,
                       final_out_carry=self.u_ogb5_carry,
                       final_out_sum=self.u_ogb5_sum,
                       shifted_out_carry=self.u_ogb5_by8_carry,
                       shifted_out_sum=self.u_ogb5_by8_sum)
        
        if self.debug_print:
            self.u_ogb5 = self.var("u_ogb5", self.inter_bit_length)
            self.wire(self.u_ogb5, self.u_ogb5_carry + self.u_ogb5_sum)
            self.u_ogb5_by8 = self.var("u_ogb5_by8", self.inter_bit_length)
            self.wire(self.u_ogb5_by8, self.u_ogb5_by8_carry + self.u_ogb5_by8_sum)

        # ((u + og_b) // 2 + og_b) // 4 = (u + 3 * og_b) // 8
        self.u_ogb3_by8_carry = self.var("u_ogb3_by8_carry", self.inter_bit_length)
        self.u_ogb3_by8_sum = self.var("u_ogb3_by8_sum", self.inter_bit_length)

        shiftu_ogb3_by8 = DW01_csa_shift_only_8(bit_length=self.inter_bit_length, debug_print=self.debug_print)
        self.add_child("shiftu_ogb3_by8",
                       shiftu_ogb3_by8,
                       final_out_carry=self.u_ogb3_carry,
                       final_out_sum=self.u_ogb3_sum,
                       shifted_out_carry=self.u_ogb3_by8_carry,
                       shifted_out_sum=self.u_ogb3_by8_sum)

        # (((u + og_b) // 2 + og_b) // 2 + og_b) // 2 = (u + 7 * og_b) // 8
        self.u_ogb7_carry = self.var("u_ogb7_carry", self.inter_bit_length)
        self.u_ogb7_sum = self.var("u_ogb7_sum", self.inter_bit_length)

        csa_u_ogb7 = DW01_csa(self.inter_bit_length, DW=self.DW)
        csa_u_ogb7.width.value = self.inter_bit_length
        self.add_child("csa_u_ogb7", 
                       csa_u_ogb7,
                       a=self.u_carry,
                       b=self.u_sum,
                       c=self.og_b7_csa,
                       ci=self.ci,
                       carry=self.u_ogb7_carry,
                       sum=self.u_ogb7_sum)

        self.u_ogb7_by8_carry = self.var("u_ogb7_by8_carry", self.inter_bit_length)
        self.u_ogb7_by8_sum = self.var("u_ogb7_by8_sum", self.inter_bit_length)

        shiftu_ogb7_by8 = DW01_csa_shift_only_8(bit_length=self.inter_bit_length, debug_print=self.debug_print)
        self.add_child("shiftu_ogb7_by8",
                       shiftu_ogb7_by8,
                       final_out_carry=self.u_ogb7_carry,
                       final_out_sum=self.u_ogb7_sum,
                       shifted_out_carry=self.u_ogb7_by8_carry,
                       shifted_out_sum=self.u_ogb7_by8_sum)

        # inv signals (control signals)
        self.inv_u_ogb_after_lsb_2 = self.var("inv_u_ogb_after_lsb_2", 1)
        self.inv_u_ogb_after_lsb_3 = self.var("inv_u_ogb_after_lsb_3", 1)

        self.u_ogb_carry_1 = self.var("u_ogb_carry_1", 3)
        self.u_ogb_sum_1 = self.var("u_ogb_sum_1", 3)

        csa_u_ogb_1 = DW01_csa(3, DW=self.DW)
        csa_u_ogb_1.width.value = 3
        self.add_child("csa_u_ogb_1", 
                       csa_u_ogb_1,
                       a=self.u_carry_by_4[2, 0],
                       b=self.u_sum_by_4[2, 0],
                       c=self.og_b_csa[2, 0],
                       ci=self.ci,
                       carry=self.u_ogb_carry_1,
                       sum=self.u_ogb_sum_1)
        
        self.u_ogb_carry_2 = self.var("u_ogb_carry_2", 3)
        self.u_ogb_sum_2 = self.var("u_ogb_sum_2", 3)

        csa_u_ogb_2 = DW01_csa(3, DW=self.DW)
        csa_u_ogb_2.width.value = 3
        self.add_child("csa_u_ogb_2", 
                       csa_u_ogb_2,
                       a=self.u_ogb2_by4_carry[2, 0],
                       b=self.u_ogb2_by4_sum[2, 0],
                       c=self.og_b_csa[2, 0],
                       ci=self.ci,
                       carry=self.u_ogb_carry_2,
                       sum=self.u_ogb_sum_2)

        self.u_ogb_carry_3 = self.var("u_ogb_carry_3", 3)
        self.u_ogb_sum_3 = self.var("u_ogb_sum_3", 3)

        csa_u_ogb_3 = DW01_csa(3, DW=self.DW)
        csa_u_ogb_3.width.value = 3
        self.add_child("csa_u_ogb_3", 
                       csa_u_ogb_3,
                       a=self.u_ogb_by4_carry[2, 0],
                       b=self.u_ogb_by4_sum[2, 0],
                       c=self.og_b_csa[2, 0],
                       ci=self.ci,
                       carry=self.u_ogb_carry_3,
                       sum=self.u_ogb_sum_3)
        
        self.u_ogb_carry_4 = self.var("u_ogb_carry_4", 3)
        self.u_ogb_sum_4 = self.var("u_ogb_sum_4", 3)

        csa_u_ogb_4 = DW01_csa(3, DW=self.DW)
        csa_u_ogb_4.width.value = 3
        self.add_child("csa_u_ogb_4", 
                       csa_u_ogb_4,
                       a=self.u_ogb3_by4_carry[2, 0],
                       b=self.u_ogb3_by4_sum[2, 0],
                       c=self.og_b_csa[2, 0],
                       ci=self.ci,
                       carry=self.u_ogb_carry_4,
                       sum=self.u_ogb_sum_4)
        
        self.u_ogb_carry_5 = self.var("u_ogb_carry_5", 3)
        self.u_ogb_sum_5 = self.var("u_ogb_sum_5", 3)

        csa_u_ogb_5 = DW01_csa(3, DW=self.DW)
        csa_u_ogb_5.width.value = 3
        self.add_child("csa_u_ogb_5", 
                       csa_u_ogb_5,
                       a=self.u_ogb_by_2_carry[2, 0],
                       b=self.u_ogb_by_2_sum[2, 0],
                       c=self.og_b_csa[2, 0],
                       ci=self.ci,
                       carry=self.u_ogb_carry_5,
                       sum=self.u_ogb_sum_5)
        
        self.u_ogb_carry_6 = self.var("u_ogb_carry_6", 3)
        self.u_ogb_sum_6 = self.var("u_ogb_sum_6", 3)

        csa_u_ogb_6 = DW01_csa(3, DW=self.DW)
        csa_u_ogb_6.width.value = 3
        self.add_child("csa_u_ogb_6", 
                       csa_u_ogb_6,
                       a=self.u_carry_by_2[2, 0],
                       b=self.u_sum_by_2[2, 0],
                       c=self.og_b_csa[2, 0],
                       ci=self.ci,
                       carry=self.u_ogb_carry_6,
                       sum=self.u_ogb_sum_6)

        if self.u_l:
            self.u_ogb_carry_7 = self.var("u_ogb_carry_7", 3)
            self.u_ogb_sum_7 = self.var("u_ogb_sum_7", 3)

            csa_u_ogb_7 = DW01_csa(3, DW=self.DW)
            csa_u_ogb_7.width.value = 3
            self.add_child("csa_u_ogb_7", 
                        csa_u_ogb_7,
                        a=self.u_delta_update_add_carry[2, 0],
                        b=self.u_delta_update_add_sum[2, 0],
                        c=self.og_b_csa[2, 0],
                        ci=self.ci,
                        carry=self.u_ogb_carry_7,
                        sum=self.u_ogb_sum_7)

            self.u_ogb_carry_8 = self.var("u_ogb_carry_8", 3)
            self.u_ogb_sum_8 = self.var("u_ogb_sum_8", 3)

            csa_u_ogb_8 = DW01_csa(3, DW=self.DW)
            csa_u_ogb_8.width.value = 3
            self.add_child("csa_u_ogb_8", 
                        csa_u_ogb_8,
                        a=self.u_delta_update_sub_first_carry[2, 0],
                        b=self.u_delta_update_sub_first_sum[2, 0],
                        c=self.og_b_csa[2, 0],
                        ci=self.ci,
                        carry=self.u_ogb_carry_8,
                        sum=self.u_ogb_sum_8)

            self.u_ogb_carry_7_by_2 = self.var("u_ogb_carry_7_by_2", 3)
            self.u_ogb_sum_7_by_2 = self.var("u_ogb_sum_7_by_2", 3)

            csa_u_ogb_7_by_2 = DW01_csa(3, DW=self.DW)
            csa_u_ogb_7_by_2.width.value = 3
            self.add_child("csa_u_ogb_7_by_2", 
                        csa_u_ogb_7_by_2,
                        a=self.u_delta_update_add_carry_by_2[2, 0],
                        b=self.u_delta_update_add_sum_by_2[2, 0],
                        c=self.og_b_csa[2, 0],
                        ci=self.ci,
                        carry=self.u_ogb_carry_7_by_2,
                        sum=self.u_ogb_sum_7_by_2)

            self.u_ogb_carry_8_by_2 = self.var("u_ogb_carry_8_by_2", 3)
            self.u_ogb_sum_8_by_2 = self.var("u_ogb_sum_8_by_2", 3)

            csa_u_ogb_8_by_2 = DW01_csa(3, DW=self.DW)
            csa_u_ogb_8_by_2.width.value = 3
            self.add_child("csa_u_ogb_8_by_2", 
                        csa_u_ogb_8_by_2,
                        a=self.u_delta_update_sub_first_carry_by_2[2, 0],
                        b=self.u_delta_update_sub_first_sum_by_2[2, 0],
                        c=self.og_b_csa[2, 0],
                        ci=self.ci,
                        carry=self.u_ogb_carry_8_by_2,
                        sum=self.u_ogb_sum_8_by_2)
            
            self.u_ogb_carry_7_ogb_by_2 = self.var("u_ogb_carry_7_ogb_by_2", 3)
            self.u_ogb_sum_7_ogb_by_2 = self.var("u_ogb_sum_7_ogb_by_2", 3)

            csa_u_ogb_7_ogb_by_2 = DW01_csa(3, DW=self.DW)
            csa_u_ogb_7_ogb_by_2.width.value = 3
            self.add_child("csa_u_ogb_7_ogb_by_2", 
                        csa_u_ogb_7_ogb_by_2,
                        a=self.u_delta_update_add_ogb_by_2_carry[2, 0],
                        b=self.u_delta_update_add_ogb_by_2_sum[2, 0],
                        c=self.og_b_csa[2, 0],
                        ci=self.ci,
                        carry=self.u_ogb_carry_7_ogb_by_2,
                        sum=self.u_ogb_sum_7_ogb_by_2)

            self.u_ogb_carry_8_ogb_by_2 = self.var("u_ogb_carry_8_ogb_by_2", 3)
            self.u_ogb_sum_8_ogb_by_2 = self.var("u_ogb_sum_8_ogb_by_2", 3)

            csa_u_ogb_8_ogb_by_2 = DW01_csa(3, DW=self.DW)
            csa_u_ogb_8_ogb_by_2.width.value = 3
            self.add_child("csa_u_ogb_8_ogb_by_2", 
                        csa_u_ogb_8_ogb_by_2,
                        a=self.u_delta_update_sub_first_ogb_by_2_carry[2, 0],
                        b=self.u_delta_update_sub_first_ogb_by_2_sum[2, 0],
                        c=self.og_b_csa[2, 0],
                        ci=self.ci,
                        carry=self.u_ogb_carry_8_ogb_by_2,
                        sum=self.u_ogb_sum_8_ogb_by_2)

            self.u_delta_update_add_carry_out = self.output("u_delta_update_add_carry_out", self.inter_bit_length)
            self.u_delta_update_add_sum_out = self.output("u_delta_update_add_sum_out", self.inter_bit_length)
            self.u_delta_update_sub_first_carry_out = self.output("u_delta_update_sub_first_carry_out", self.inter_bit_length)
            self.u_delta_update_sub_first_sum_out = self.output("u_delta_update_sub_first_sum_out", self.inter_bit_length)

            self.wire(self.u_delta_update_add_carry_out, self.u_delta_update_add_carry)
            self.wire(self.u_delta_update_add_sum_out, self.u_delta_update_add_sum)
            self.wire(self.u_delta_update_sub_first_carry_out, self.u_delta_update_sub_first_carry)
            self.wire(self.u_delta_update_sub_first_sum_out, self.u_delta_update_sub_first_sum)
            
            self.u_delta_update_add_carry_by_2_out = self.output("u_delta_update_add_carry_by_2_out", self.inter_bit_length)
            self.u_delta_update_add_sum_by_2_out = self.output("u_delta_update_add_sum_by_2_out", self.inter_bit_length)
            self.u_delta_update_sub_first_carry_by_2_out = self.output("u_delta_update_sub_first_carry_by_2_out", self.inter_bit_length)
            self.u_delta_update_sub_first_sum_by_2_out = self.output("u_delta_update_sub_first_sum_by_2_out", self.inter_bit_length)
            
            self.wire(self.u_delta_update_add_carry_by_2_out, self.u_delta_update_add_carry_by_2)
            self.wire(self.u_delta_update_add_sum_by_2_out, self.u_delta_update_add_sum_by_2)
            self.wire(self.u_delta_update_sub_first_carry_by_2_out, self.u_delta_update_sub_first_carry_by_2)
            self.wire(self.u_delta_update_sub_first_sum_by_2_out, self.u_delta_update_sub_first_sum_by_2)

            self.u_delta_update_add_ogb_by_2_carry_out = self.output("u_delta_update_add_ogb_by_2_carry_out", self.inter_bit_length)
            self.u_delta_update_add_ogb_by_2_sum_out = self.output("u_delta_update_add_ogb_by_2_sum_out", self.inter_bit_length)
            self.u_delta_update_sub_first_ogb_by_2_carry_out = self.output("u_delta_update_sub_first_ogb_by_2_carry_out", self.inter_bit_length)
            self.u_delta_update_sub_first_ogb_by_2_sum_out = self.output("u_delta_update_sub_first_ogb_by_2_sum_out", self.inter_bit_length)
            
            self.wire(self.u_delta_update_add_ogb_by_2_carry_out, self.u_delta_update_add_ogb_by_2_carry)
            self.wire(self.u_delta_update_add_ogb_by_2_sum_out, self.u_delta_update_add_ogb_by_2_sum)
            self.wire(self.u_delta_update_sub_first_ogb_by_2_carry_out, self.u_delta_update_sub_first_ogb_by_2_carry)
            self.wire(self.u_delta_update_sub_first_ogb_by_2_sum_out, self.u_delta_update_sub_first_ogb_by_2_sum)

            self.u_ogb_carry_7_out = self.output("u_ogb_carry_7_out", 3)
            self.u_ogb_sum_7_out = self.output("u_ogb_sum_7_out", 3)
            self.u_ogb_carry_8_out = self.output("u_ogb_carry_8_out", 3)
            self.u_ogb_sum_8_out = self.output("u_ogb_sum_8_out", 3)
            
            self.wire(self.u_ogb_carry_7_out, self.u_ogb_carry_7)
            self.wire(self.u_ogb_sum_7_out, self.u_ogb_sum_7)
            self.wire(self.u_ogb_carry_8_out, self.u_ogb_carry_8)
            self.wire(self.u_ogb_sum_8_out, self.u_ogb_sum_8)

            self.u_ogb_carry_7_by_2_out = self.output("u_ogb_carry_7_by_2_out", 3)
            self.u_ogb_sum_7_by_2_out = self.output("u_ogb_sum_7_by_2_out", 3)
            self.u_ogb_carry_8_by_2_out = self.output("u_ogb_carry_8_by_2_out", 3)
            self.u_ogb_sum_8_by_2_out = self.output("u_ogb_sum_8_by_2_out", 3)
            
            self.wire(self.u_ogb_carry_7_by_2_out, self.u_ogb_carry_7_by_2)
            self.wire(self.u_ogb_sum_7_by_2_out, self.u_ogb_sum_7_by_2)
            self.wire(self.u_ogb_carry_8_by_2_out, self.u_ogb_carry_8_by_2)
            self.wire(self.u_ogb_sum_8_by_2_out, self.u_ogb_sum_8_by_2)

            self.u_ogb_carry_7_ogb_by_2_out = self.output("u_ogb_carry_7_ogb_by_2_out", 3)
            self.u_ogb_sum_7_ogb_by_2_out = self.output("u_ogb_sum_7_ogb_by_2_out", 3)
            self.u_ogb_carry_8_ogb_by_2_out = self.output("u_ogb_carry_8_ogb_by_2_out", 3)
            self.u_ogb_sum_8_ogb_by_2_out = self.output("u_ogb_sum_8_ogb_by_2_out", 3)
            
            self.wire(self.u_ogb_carry_7_ogb_by_2_out, self.u_ogb_carry_7_ogb_by_2)
            self.wire(self.u_ogb_sum_7_ogb_by_2_out, self.u_ogb_sum_7_ogb_by_2)
            self.wire(self.u_ogb_carry_8_ogb_by_2_out, self.u_ogb_carry_8_ogb_by_2)
            self.wire(self.u_ogb_sum_8_ogb_by_2_out, self.u_ogb_sum_8_ogb_by_2)

        else:
            self.u_delta_update_add_even = self.input("u_delta_update_add_even", 1)
            self.u_delta_update_sub_first_even = self.input("u_delta_update_sub_first_even", 1)

            self.u_delta_update_add_carry_out = self.input("u_delta_update_add_carry_out", self.inter_bit_length)
            self.u_delta_update_add_sum_out = self.input("u_delta_update_add_sum_out", self.inter_bit_length)
            self.u_delta_update_sub_first_carry_out = self.input("u_delta_update_sub_first_carry_out", self.inter_bit_length)
            self.u_delta_update_sub_first_sum_out = self.input("u_delta_update_sub_first_sum_out", self.inter_bit_length)
            
            self.u_delta_update_add_carry_by_2_out = self.input("u_delta_update_add_carry_by_2_out", self.inter_bit_length)
            self.u_delta_update_add_sum_by_2_out = self.input("u_delta_update_add_sum_by_2_out", self.inter_bit_length)
            self.u_delta_update_sub_first_carry_by_2_out = self.input("u_delta_update_sub_first_carry_by_2_out", self.inter_bit_length)
            self.u_delta_update_sub_first_sum_by_2_out = self.input("u_delta_update_sub_first_sum_by_2_out", self.inter_bit_length)
            
            self.u_delta_update_add_ogb_by_2_carry_out = self.input("u_delta_update_add_ogb_by_2_carry_out", self.inter_bit_length)
            self.u_delta_update_add_ogb_by_2_sum_out = self.input("u_delta_update_add_ogb_by_2_sum_out", self.inter_bit_length)
            self.u_delta_update_sub_first_ogb_by_2_carry_out = self.input("u_delta_update_sub_first_ogb_by_2_carry_out", self.inter_bit_length)
            self.u_delta_update_sub_first_ogb_by_2_sum_out = self.input("u_delta_update_sub_first_ogb_by_2_sum_out", self.inter_bit_length)
            
            self.u_ogb_carry_7_out = self.input("u_ogb_carry_7_out", 3)
            self.u_ogb_sum_7_out = self.input("u_ogb_sum_7_out", 3)
            self.u_ogb_carry_8_out = self.input("u_ogb_carry_8_out", 3)
            self.u_ogb_sum_8_out = self.input("u_ogb_sum_8_out", 3)

            self.u_ogb_carry_7_by_2_out = self.input("u_ogb_carry_7_by_2_out", 3)
            self.u_ogb_sum_7_by_2_out = self.input("u_ogb_sum_7_by_2_out", 3)
            self.u_ogb_carry_8_by_2_out = self.input("u_ogb_carry_8_by_2_out", 3)
            self.u_ogb_sum_8_by_2_out = self.input("u_ogb_sum_8_by_2_out", 3)

            self.u_ogb_carry_7_ogb_by_2_out = self.input("u_ogb_carry_7_ogb_by_2_out", 3)
            self.u_ogb_sum_7_ogb_by_2_out = self.input("u_ogb_sum_7_ogb_by_2_out", 3)
            self.u_ogb_carry_8_ogb_by_2_out = self.input("u_ogb_carry_8_ogb_by_2_out", 3)
            self.u_ogb_sum_8_ogb_by_2_out = self.input("u_ogb_sum_8_ogb_by_2_out", 3)

        # divby8 u_ogb signals

        self.u_ogb_8_carry_1 = self.var("u_ogb_8_carry_1", 3)
        self.u_ogb_8_sum_1 = self.var("u_ogb_8_sum_1", 3)

        csa_u_ogb_8_1 = DW01_csa(3, DW=self.DW)
        csa_u_ogb_8_1.width.value = 3
        self.add_child("csa_u_ogb_8_1", 
                       csa_u_ogb_8_1,
                       a=self.u_carry_by_8[2, 0],
                       b=self.u_sum_by_8[2, 0],
                       c=self.og_b_csa[2, 0],
                       ci=self.ci,
                       carry=self.u_ogb_8_carry_1,
                       sum=self.u_ogb_8_sum_1)

        self.u_ogb_8_carry_2 = self.var("u_ogb_8_carry_2", 3)
        self.u_ogb_8_sum_2 = self.var("u_ogb_8_sum_2", 3)

        csa_u_ogb_8_2 = DW01_csa(3, DW=self.DW)
        csa_u_ogb_8_2.width.value = 3
        self.add_child("csa_u_ogb_8_2", 
                       csa_u_ogb_8_2,
                       a=self.u_ogb4_by_8_carry[2, 0],
                       b=self.u_ogb4_by_8_sum[2, 0],
                       c=self.og_b_csa[2, 0],
                       ci=self.ci,
                       carry=self.u_ogb_8_carry_2,
                       sum=self.u_ogb_8_sum_2)
        
        self.u_ogb_8_carry_3 = self.var("u_ogb_8_carry_3", 3)
        self.u_ogb_8_sum_3 = self.var("u_ogb_8_sum_3", 3)

        csa_u_ogb_8_3 = DW01_csa(3, DW=self.DW)
        csa_u_ogb_8_3.width.value = 3
        self.add_child("csa_u_ogb_8_3", 
                       csa_u_ogb_8_3,
                       a=self.u_ogb2_by8_carry[2, 0],
                       b=self.u_ogb2_by8_sum[2, 0],
                       c=self.og_b_csa[2, 0],
                       ci=self.ci,
                       carry=self.u_ogb_8_carry_3,
                       sum=self.u_ogb_8_sum_3)
        
        self.u_ogb_8_carry_4 = self.var("u_ogb_8_carry_4", 3)
        self.u_ogb_8_sum_4 = self.var("u_ogb_8_sum_4", 3)

        csa_u_ogb_8_4 = DW01_csa(3, DW=self.DW)
        csa_u_ogb_8_4.width.value = 3
        self.add_child("csa_u_ogb_8_4", 
                       csa_u_ogb_8_4,
                       a=self.u_ogb6_by8_carry[2, 0],
                       b=self.u_ogb6_by8_sum[2, 0],
                       c=self.og_b_csa[2, 0],
                       ci=self.ci,
                       carry=self.u_ogb_8_carry_4,
                       sum=self.u_ogb_8_sum_4)

        self.u_ogb_8_carry_5 = self.var("u_ogb_8_carry_5", 3)
        self.u_ogb_8_sum_5 = self.var("u_ogb_8_sum_5", 3)

        csa_u_ogb_8_5 = DW01_csa(3, DW=self.DW)
        csa_u_ogb_8_5.width.value = 3
        self.add_child("csa_u_ogb_8_5", 
                       csa_u_ogb_8_5,
                       a=self.u_ogb_by8_carry[2, 0],
                       b=self.u_ogb_by8_sum[2, 0],
                       c=self.og_b_csa[2, 0],
                       ci=self.ci,
                       carry=self.u_ogb_8_carry_5,
                       sum=self.u_ogb_8_sum_5)

        self.u_ogb_8_carry_6 = self.var("u_ogb_8_carry_6", 3)
        self.u_ogb_8_sum_6 = self.var("u_ogb_8_sum_6", 3)

        csa_u_ogb_8_6 = DW01_csa(3, DW=self.DW)
        csa_u_ogb_8_6.width.value = 3
        self.add_child("csa_u_ogb_8_6", 
                       csa_u_ogb_8_6,
                       a=self.u_ogb5_by8_carry[2, 0],
                       b=self.u_ogb5_by8_sum[2, 0],
                       c=self.og_b_csa[2, 0],
                       ci=self.ci,
                       carry=self.u_ogb_8_carry_6,
                       sum=self.u_ogb_8_sum_6)

        self.u_ogb_8_carry_7 = self.var("u_ogb_8_carry_7", 3)
        self.u_ogb_8_sum_7 = self.var("u_ogb_8_sum_7", 3)

        csa_u_ogb_8_7 = DW01_csa(3, DW=self.DW)
        csa_u_ogb_8_7.width.value = 3
        self.add_child("csa_u_ogb_8_7", 
                       csa_u_ogb_8_7,
                       a=self.u_ogb3_by8_carry[2, 0],
                       b=self.u_ogb3_by8_sum[2, 0],
                       c=self.og_b_csa[2, 0],
                       ci=self.ci,
                       carry=self.u_ogb_8_carry_7,
                       sum=self.u_ogb_8_sum_7)

        self.u_ogb_8_carry_8 = self.var("u_ogb_8_carry_8", 3)
        self.u_ogb_8_sum_8 = self.var("u_ogb_8_sum_8", 3)

        csa_u_ogb_8_8 = DW01_csa(3, DW=self.DW)
        csa_u_ogb_8_8.width.value = 3
        self.add_child("csa_u_ogb_8_8", 
                       csa_u_ogb_8_8,
                       a=self.u_ogb7_by8_carry[2, 0],
                       b=self.u_ogb7_by8_sum[2, 0],
                       c=self.og_b_csa[2, 0],
                       ci=self.ci,
                       carry=self.u_ogb_8_carry_8,
                       sum=self.u_ogb_8_sum_8)

        # u + y lsb
        self.uy_after_carry1 = self.var("uy_after_carry1", 2)
        self.uy_after_sum1 = self.var("uy_after_sum1", 2)

        uy_after1 = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_after1",
                        uy_after1,
                        a_carry=self.u_carry_by_4[1, 0],
                        a_sum=self.u_sum_by_4[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry1,
                        final_out_sum=self.uy_after_sum1)

        self.uy_after_carry2 = self.var("uy_after_carry2", 2)
        self.uy_after_sum2 = self.var("uy_after_sum2", 2)

        uy_after2 = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_after2",
                        uy_after2,
                        a_carry=self.u_ogb2_by4_carry[1, 0],
                        a_sum=self.u_ogb2_by4_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry2,
                        final_out_sum=self.uy_after_sum2)
        
        self.uy_after_carry3 = self.var("uy_after_carry3", 2)
        self.uy_after_sum3 = self.var("uy_after_sum3", 2)

        uy_after3 = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_after3",
                        uy_after3,
                        a_carry=self.u_ogb_by4_carry[1, 0],
                        a_sum=self.u_ogb_by4_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry3,
                        final_out_sum=self.uy_after_sum3)

        self.uy_after_carry4 = self.var("uy_after_carry4", 2)
        self.uy_after_sum4 = self.var("uy_after_sum4", 2)

        uy_after4 = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_after4",
                        uy_after4,
                        a_carry=self.u_ogb3_by4_carry[1, 0],
                        a_sum=self.u_ogb3_by4_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry4,
                        final_out_sum=self.uy_after_sum4)
        
        self.uy_after_carry5 = self.var("uy_after_carry5", 2)
        self.uy_after_sum5 = self.var("uy_after_sum5", 2)

        uy_after5 = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_after5",
                        uy_after5,
                        a_carry=self.u_ogb_by_2_carry[1, 0],
                        a_sum=self.u_ogb_by_2_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry5,
                        final_out_sum=self.uy_after_sum5)
        
        self.uy_after_carry6 = self.var("uy_after_carry6", 2)
        self.uy_after_sum6 = self.var("uy_after_sum6", 2)

        uy_after6 = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_after6",
                        uy_after6,
                        a_carry=self.u_carry_by_2[1, 0],
                        a_sum=self.u_sum_by_2[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry6,
                        final_out_sum=self.uy_after_sum6)

        self.uy_add_after_carry = self.var("uy_add_after_carry", 2)
        self.uy_add_after_sum = self.var("uy_add_after_sum", 2)

        uy_add_after = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_add_after",
                        uy_add_after,
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_add_after_carry,
                        final_out_sum=self.uy_add_after_sum)
        
        self.uy_sub_after_carry = self.var("uy_sub_after_carry", 2)
        self.uy_sub_after_sum = self.var("uy_sub_after_sum", 2)

        uy_sub_after = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_sub_after",
                        uy_sub_after,
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_sub_after_carry,
                        final_out_sum=self.uy_sub_after_sum)
        
        self.uy_add_after_by_2_carry = self.var("uy_add_after_by_2_carry", 2)
        self.uy_add_after_by_2_sum = self.var("uy_add_after_by_2_sum", 2)

        uy_add_after_by_2 = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_add_after_by_2",
                        uy_add_after_by_2,
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_add_after_by_2_carry,
                        final_out_sum=self.uy_add_after_by_2_sum)
        
        self.uy_sub_after_by_2_carry = self.var("uy_sub_after_by_2_carry", 2)
        self.uy_sub_after_by_2_sum = self.var("uy_sub_after_by_2_sum", 2)

        uy_sub_after_by_2 = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_sub_after_by_2",
                        uy_sub_after_by_2,
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_sub_after_by_2_carry,
                        final_out_sum=self.uy_sub_after_by_2_sum)
        
        self.uy_add_after_ogb_by_2_carry = self.var("uy_add_after_ogb_by_2_carry", 2)
        self.uy_add_after_ogb_by_2_sum = self.var("uy_add_after_ogb_by_2_sum", 2)

        uy_add_after_ogb_by_2 = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_add_after_ogb_by_2",
                        uy_add_after_ogb_by_2,
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_add_after_ogb_by_2_carry,
                        final_out_sum=self.uy_add_after_ogb_by_2_sum)
        
        self.uy_sub_after_ogb_by_2_carry = self.var("uy_sub_after_ogb_by_2_carry", 2)
        self.uy_sub_after_ogb_by_2_sum = self.var("uy_sub_after_ogb_by_2_sum", 2)

        uy_sub_after_ogb_by_2 = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_sub_after_ogb_by_2",
                        uy_sub_after_ogb_by_2,
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_sub_after_ogb_by_2_carry,
                        final_out_sum=self.uy_sub_after_ogb_by_2_sum)
        
        if self.u_l:
            self.wire(uy_add_after.ports.a_carry, self.u_delta_update_add_carry[1, 0])
            self.wire(uy_add_after.ports.a_sum, self.u_delta_update_add_sum[1, 0])
            self.wire(uy_sub_after.ports.a_carry, self.u_delta_update_sub_first_carry[1, 0])
            self.wire(uy_sub_after.ports.a_sum, self.u_delta_update_sub_first_sum[1, 0])

            self.wire(uy_add_after_by_2.ports.a_carry, self.u_delta_update_add_carry_by_2[1, 0])
            self.wire(uy_add_after_by_2.ports.a_sum, self.u_delta_update_add_sum_by_2[1, 0])
            self.wire(uy_sub_after_by_2.ports.a_carry, self.u_delta_update_sub_first_carry_by_2[1, 0])
            self.wire(uy_sub_after_by_2.ports.a_sum, self.u_delta_update_sub_first_sum_by_2[1, 0])

            self.wire(uy_add_after_ogb_by_2.ports.a_carry, self.u_delta_update_add_ogb_by_2_carry[1, 0])
            self.wire(uy_add_after_ogb_by_2.ports.a_sum, self.u_delta_update_add_ogb_by_2_sum[1, 0])
            self.wire(uy_sub_after_ogb_by_2.ports.a_carry, self.u_delta_update_sub_first_ogb_by_2_carry[1, 0])
            self.wire(uy_sub_after_ogb_by_2.ports.a_sum, self.u_delta_update_sub_first_ogb_by_2_sum[1, 0])
        else:
            self.wire(uy_add_after.ports.a_carry, self.u_delta_update_add_carry_out[1, 0])
            self.wire(uy_add_after.ports.a_sum, self.u_delta_update_add_sum_out[1, 0])
            self.wire(uy_sub_after.ports.a_carry, self.u_delta_update_sub_first_carry_out[1, 0])
            self.wire(uy_sub_after.ports.a_sum, self.u_delta_update_sub_first_sum_out[1, 0])

            self.wire(uy_add_after_by_2.ports.a_carry, self.u_delta_update_add_carry_by_2_out[1, 0])
            self.wire(uy_add_after_by_2.ports.a_sum, self.u_delta_update_add_sum_by_2_out[1, 0])
            self.wire(uy_sub_after_by_2.ports.a_carry, self.u_delta_update_sub_first_carry_by_2_out[1, 0])
            self.wire(uy_sub_after_by_2.ports.a_sum, self.u_delta_update_sub_first_sum_by_2_out[1, 0])

            self.wire(uy_add_after_ogb_by_2.ports.a_carry, self.u_delta_update_add_ogb_by_2_carry_out[1, 0])
            self.wire(uy_add_after_ogb_by_2.ports.a_sum, self.u_delta_update_add_ogb_by_2_sum_out[1, 0])
            self.wire(uy_sub_after_ogb_by_2.ports.a_carry, self.u_delta_update_sub_first_ogb_by_2_carry_out[1, 0])
            self.wire(uy_sub_after_ogb_by_2.ports.a_sum, self.u_delta_update_sub_first_ogb_by_2_sum_out[1, 0])
        
        # divby8 u + y
        self.uy_after_carry_8_1 = self.var("uy_after_carry_8_1", 2)
        self.uy_after_sum_8_1 = self.var("uy_after_sum_8_1", 2)

        uy_after_8_1 = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_after_8_1",
                        uy_after_8_1,
                        a_carry=self.u_carry_by_8[1, 0],
                        a_sum=self.u_sum_by_8[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry_8_1,
                        final_out_sum=self.uy_after_sum_8_1)

        self.uy_after_carry_8_2 = self.var("uy_after_carry_8_2", 2)
        self.uy_after_sum_8_2 = self.var("uy_after_sum_8_2", 2)

        uy_after_8_2 = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_after_8_2",
                        uy_after_8_2,
                        a_carry=self.u_ogb4_by_8_carry[1, 0],
                        a_sum=self.u_ogb4_by_8_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry_8_2,
                        final_out_sum=self.uy_after_sum_8_2)

        self.uy_after_carry_8_3 = self.var("uy_after_carry_8_3", 2)
        self.uy_after_sum_8_3 = self.var("uy_after_sum_8_3", 2)

        uy_after_8_3 = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_after_8_3",
                        uy_after_8_3,
                        a_carry=self.u_ogb2_by8_carry[1, 0],
                        a_sum=self.u_ogb2_by8_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry_8_3,
                        final_out_sum=self.uy_after_sum_8_3)
        
        self.uy_after_carry_8_4 = self.var("uy_after_carry_8_4", 2)
        self.uy_after_sum_8_4 = self.var("uy_after_sum_8_4", 2)

        uy_after_8_4 = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_after_8_4",
                        uy_after_8_4,
                        a_carry=self.u_ogb6_by8_carry[1, 0],
                        a_sum=self.u_ogb6_by8_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry_8_4,
                        final_out_sum=self.uy_after_sum_8_4)

        self.uy_after_carry_8_5 = self.var("uy_after_carry_8_5", 2)
        self.uy_after_sum_8_5 = self.var("uy_after_sum_8_5", 2)

        uy_after_8_5 = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_after_8_5",
                        uy_after_8_5,
                        a_carry=self.u_ogb_by8_carry[1, 0],
                        a_sum=self.u_ogb_by8_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry_8_5,
                        final_out_sum=self.uy_after_sum_8_5)
        
        self.uy_after_carry_8_6 = self.var("uy_after_carry_8_6", 2)
        self.uy_after_sum_8_6 = self.var("uy_after_sum_8_6", 2)

        uy_after_8_6 = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_after_8_6",
                        uy_after_8_6,
                        a_carry=self.u_ogb5_by8_carry[1, 0],
                        a_sum=self.u_ogb5_by8_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry_8_6,
                        final_out_sum=self.uy_after_sum_8_6)
        
        self.uy_after_carry_8_7 = self.var("uy_after_carry_8_7", 2)
        self.uy_after_sum_8_7 = self.var("uy_after_sum_8_7", 2)

        uy_after_8_7 = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_after_8_7",
                        uy_after_8_7,
                        a_carry=self.u_ogb3_by8_carry[1, 0],
                        a_sum=self.u_ogb3_by8_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry_8_7,
                        final_out_sum=self.uy_after_sum_8_7)
        
        self.uy_after_carry_8_8 = self.var("uy_after_carry_8_8", 2)
        self.uy_after_sum_8_8 = self.var("uy_after_sum_8_8", 2)

        uy_after_8_8 = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_after_8_8",
                        uy_after_8_8,
                        a_carry=self.u_ogb7_by8_carry[1, 0],
                        a_sum=self.u_ogb7_by8_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry_8_8,
                        final_out_sum=self.uy_after_sum_8_8)

        # sub u - y
        self.uy_after_carry1_sub = self.var("uy_after_carry1_sub", 2)
        self.uy_after_sum1_sub = self.var("uy_after_sum1_sub", 2)

        uy_after1_sub = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after1_sub",
                        uy_after1_sub,
                        a_carry=self.u_carry_by_4[1, 0],
                        a_sum=self.u_sum_by_4[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry1_sub,
                        final_out_sum=self.uy_after_sum1_sub)

        self.uy_after_carry2_sub = self.var("uy_after_carry2_sub", 2)
        self.uy_after_sum2_sub = self.var("uy_after_sum2_sub", 2)

        uy_after2_sub = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after2_sub",
                        uy_after2_sub,
                        a_carry=self.u_ogb2_by4_carry[1, 0],
                        a_sum=self.u_ogb2_by4_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry2_sub,
                        final_out_sum=self.uy_after_sum2_sub)
        
        self.uy_after_carry3_sub = self.var("uy_after_carry3_sub", 2)
        self.uy_after_sum3_sub = self.var("uy_after_sum3_sub", 2)

        uy_after3_sub = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after3_sub",
                        uy_after3_sub,
                        a_carry=self.u_ogb_by4_carry[1, 0],
                        a_sum=self.u_ogb_by4_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry3_sub,
                        final_out_sum=self.uy_after_sum3_sub)

        self.uy_after_carry4_sub = self.var("uy_after_carry4_sub", 2)
        self.uy_after_sum4_sub = self.var("uy_after_sum4_sub", 2)

        uy_after4_sub = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after4_sub",
                        uy_after4_sub,
                        a_carry=self.u_ogb3_by4_carry[1, 0],
                        a_sum=self.u_ogb3_by4_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry4_sub,
                        final_out_sum=self.uy_after_sum4_sub)
        
        self.uy_after_carry5_sub = self.var("uy_after_carry5_sub", 2)
        self.uy_after_sum5_sub = self.var("uy_after_sum5_sub", 2)

        uy_after5_sub = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after5_sub",
                        uy_after5_sub,
                        a_carry=self.u_ogb_by_2_carry[1, 0],
                        a_sum=self.u_ogb_by_2_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry5_sub,
                        final_out_sum=self.uy_after_sum5_sub)
        
        self.uy_after_carry6_sub = self.var("uy_after_carry6_sub", 2)
        self.uy_after_sum6_sub = self.var("uy_after_sum6_sub", 2)

        uy_after6_sub = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after6_sub",
                        uy_after6_sub,
                        a_carry=self.u_carry_by_2[1, 0],
                        a_sum=self.u_sum_by_2[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry6_sub,
                        final_out_sum=self.uy_after_sum6_sub)

        self.uy_add_after_carry_sub = self.var("uy_add_after_carry_sub", 2)
        self.uy_add_after_sum_sub = self.var("uy_add_after_sum_sub", 2)

        uy_add_after_sub = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_add_after_sub",
                        uy_add_after_sub,
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_add_after_carry_sub,
                        final_out_sum=self.uy_add_after_sum_sub)
        
        self.uy_sub_after_carry_sub = self.var("uy_sub_after_carry_sub", 2)
        self.uy_sub_after_sum_sub = self.var("uy_sub_after_sum_sub", 2)

        uy_sub_after_sub = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_sub_after_sub",
                        uy_sub_after_sub,
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_sub_after_carry_sub,
                        final_out_sum=self.uy_sub_after_sum_sub)
        
        self.uy_add_after_by_2_carry_sub = self.var("uy_add_after_by_2_carry_sub", 2)
        self.uy_add_after_by_2_sum_sub = self.var("uy_add_after_by_2_sum_sub", 2)

        uy_add_after_by_2_sub = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_add_after_by_2_sub",
                        uy_add_after_by_2_sub,
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_add_after_by_2_carry_sub,
                        final_out_sum=self.uy_add_after_by_2_sum_sub)
        
        self.uy_sub_after_by_2_carry_sub = self.var("uy_sub_after_by_2_carry_sub", 2)
        self.uy_sub_after_by_2_sum_sub = self.var("uy_sub_after_by_2_sum_sub", 2)

        uy_sub_after_by_2_sub = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_sub_after_by_2_sub",
                        uy_sub_after_by_2_sub,
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_sub_after_by_2_carry_sub,
                        final_out_sum=self.uy_sub_after_by_2_sum_sub)
        
        self.uy_add_after_ogb_by_2_carry_sub = self.var("uy_add_after_ogb_by_2_carry_sub", 2)
        self.uy_add_after_ogb_by_2_sum_sub = self.var("uy_add_after_ogb_by_2_sum_sub", 2)

        uy_add_after_ogb_by_2_sub = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_add_after_ogb_by_2_sub",
                        uy_add_after_ogb_by_2_sub,
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_add_after_ogb_by_2_carry_sub,
                        final_out_sum=self.uy_add_after_ogb_by_2_sum_sub)
        
        self.uy_sub_after_ogb_by_2_carry_sub = self.var("uy_sub_after_ogb_by_2_carry_sub", 2)
        self.uy_sub_after_ogb_by_2_sum_sub = self.var("uy_sub_after_ogb_by_2_sum_sub", 2)

        uy_sub_after_ogb_by_2_sub = DW01_csa_4(2, True, DW=self.DW)
        self.add_child("uy_sub_after_ogb_by_2_sub",
                        uy_sub_after_ogb_by_2_sub,
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_sub_after_ogb_by_2_carry_sub,
                        final_out_sum=self.uy_sub_after_ogb_by_2_sum_sub)   

        if self.u_l:
            self.wire(uy_add_after_sub.ports.a_carry, self.u_delta_update_add_carry[1, 0])
            self.wire(uy_add_after_sub.ports.a_sum, self.u_delta_update_add_sum[1, 0])
            self.wire(uy_sub_after_sub.ports.a_carry, self.u_delta_update_sub_first_carry[1, 0])
            self.wire(uy_sub_after_sub.ports.a_sum, self.u_delta_update_sub_first_sum[1, 0])

            self.wire(uy_add_after_by_2_sub.ports.a_carry, self.u_delta_update_add_carry_by_2[1, 0])
            self.wire(uy_add_after_by_2_sub.ports.a_sum, self.u_delta_update_add_sum_by_2[1, 0])
            self.wire(uy_sub_after_by_2_sub.ports.a_carry, self.u_delta_update_sub_first_carry_by_2[1, 0])
            self.wire(uy_sub_after_by_2_sub.ports.a_sum, self.u_delta_update_sub_first_sum_by_2[1, 0])

            self.wire(uy_add_after_ogb_by_2_sub.ports.a_carry, self.u_delta_update_add_ogb_by_2_carry[1, 0])
            self.wire(uy_add_after_ogb_by_2_sub.ports.a_sum, self.u_delta_update_add_ogb_by_2_sum[1, 0])
            self.wire(uy_sub_after_ogb_by_2_sub.ports.a_carry, self.u_delta_update_sub_first_ogb_by_2_carry[1, 0])
            self.wire(uy_sub_after_ogb_by_2_sub.ports.a_sum, self.u_delta_update_sub_first_ogb_by_2_sum[1, 0])
        else:
            self.wire(uy_add_after_sub.ports.a_carry, self.u_delta_update_add_carry_out[1, 0])
            self.wire(uy_add_after_sub.ports.a_sum, self.u_delta_update_add_sum_out[1, 0])
            self.wire(uy_sub_after_sub.ports.a_carry, self.u_delta_update_sub_first_carry_out[1, 0])
            self.wire(uy_sub_after_sub.ports.a_sum, self.u_delta_update_sub_first_sum_out[1, 0])

            self.wire(uy_add_after_by_2_sub.ports.a_carry, self.u_delta_update_add_carry_by_2_out[1, 0])
            self.wire(uy_add_after_by_2_sub.ports.a_sum, self.u_delta_update_add_sum_by_2_out[1, 0])
            self.wire(uy_sub_after_by_2_sub.ports.a_carry, self.u_delta_update_sub_first_carry_by_2_out[1, 0])
            self.wire(uy_sub_after_by_2_sub.ports.a_sum, self.u_delta_update_sub_first_sum_by_2_out[1, 0])

            self.wire(uy_add_after_ogb_by_2_sub.ports.a_carry, self.u_delta_update_add_ogb_by_2_carry_out[1, 0])
            self.wire(uy_add_after_ogb_by_2_sub.ports.a_sum, self.u_delta_update_add_ogb_by_2_sum_out[1, 0])
            self.wire(uy_sub_after_ogb_by_2_sub.ports.a_carry, self.u_delta_update_sub_first_ogb_by_2_carry_out[1, 0])
            self.wire(uy_sub_after_ogb_by_2_sub.ports.a_sum, self.u_delta_update_sub_first_ogb_by_2_sum_out[1, 0])

        # divby8 u - y
        self.uy_after_sub_carry_8_1 = self.var("uy_after_sub_carry_8_1", 2)
        self.uy_after_sub_sum_8_1 = self.var("uy_after_sub_sum_8_1", 2)

        uy_after_sub_8_1 = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after_sub_8_1",
                        uy_after_sub_8_1,
                        a_carry=self.u_carry_by_8[1, 0],
                        a_sum=self.u_sum_by_8[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_sub_carry_8_1,
                        final_out_sum=self.uy_after_sub_sum_8_1)

        self.uy_after_sub_carry_8_2 = self.var("uy_after_sub_carry_8_2", 2)
        self.uy_after_sub_sum_8_2 = self.var("uy_after_sub_sum_8_2", 2)

        uy_after_sub_8_2 = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after_sub_8_2",
                        uy_after_sub_8_2,
                        a_carry=self.u_ogb4_by_8_carry[1, 0],
                        a_sum=self.u_ogb4_by_8_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_sub_carry_8_2,
                        final_out_sum=self.uy_after_sub_sum_8_2)

        self.uy_after_sub_carry_8_3 = self.var("uy_after_sub_carry_8_3", 2)
        self.uy_after_sub_sum_8_3 = self.var("uy_after_sub_sum_8_3", 2)

        uy_after_sub_8_3 = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after_sub_8_3",
                        uy_after_sub_8_3,
                        a_carry=self.u_ogb2_by8_carry[1, 0],
                        a_sum=self.u_ogb2_by8_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_sub_carry_8_3,
                        final_out_sum=self.uy_after_sub_sum_8_3)
        
        self.uy_after_sub_carry_8_4 = self.var("uy_after_sub_carry_8_4", 2)
        self.uy_after_sub_sum_8_4 = self.var("uy_after_sub_sum_8_4", 2)

        uy_after_sub_8_4 = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after_sub_8_4",
                        uy_after_sub_8_4,
                        a_carry=self.u_ogb6_by8_carry[1, 0],
                        a_sum=self.u_ogb6_by8_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_sub_carry_8_4,
                        final_out_sum=self.uy_after_sub_sum_8_4)

        self.uy_after_sub_carry_8_5 = self.var("uy_after_sub_carry_8_5", 2)
        self.uy_after_sub_sum_8_5 = self.var("uy_after_sub_sum_8_5", 2)

        uy_after_sub_8_5 = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after_sub_8_5",
                        uy_after_sub_8_5,
                        a_carry=self.u_ogb_by8_carry[1, 0],
                        a_sum=self.u_ogb_by8_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_sub_carry_8_5,
                        final_out_sum=self.uy_after_sub_sum_8_5)
        
        self.uy_after_sub_carry_8_6 = self.var("uy_after_sub_carry_8_6", 2)
        self.uy_after_sub_sum_8_6 = self.var("uy_after_sub_sum_8_6", 2)

        uy_after_sub_8_6 = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after_sub_8_6",
                        uy_after_sub_8_6,
                        a_carry=self.u_ogb5_by8_carry[1, 0],
                        a_sum=self.u_ogb5_by8_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_sub_carry_8_6,
                        final_out_sum=self.uy_after_sub_sum_8_6)
        
        self.uy_after_sub_carry_8_7 = self.var("uy_after_sub_carry_8_7", 2)
        self.uy_after_sub_sum_8_7 = self.var("uy_after_sub_sum_8_7", 2)

        uy_after_sub_8_7 = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after_sub_8_7",
                        uy_after_sub_8_7,
                        a_carry=self.u_ogb3_by8_carry[1, 0],
                        a_sum=self.u_ogb3_by8_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_sub_carry_8_7,
                        final_out_sum=self.uy_after_sub_sum_8_7)
        
        self.uy_after_sub_carry_8_8 = self.var("uy_after_sub_carry_8_8", 2)
        self.uy_after_sub_sum_8_8 = self.var("uy_after_sub_sum_8_8", 2)

        uy_after_sub_8_8 = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after_sub_8_8",
                        uy_after_sub_8_8,
                        a_carry=self.u_ogb7_by8_carry[1, 0],
                        a_sum=self.u_ogb7_by8_sum[1, 0],
                        b_carry=self.y_carry_in[1, 0],
                        b_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_sub_carry_8_8,
                        final_out_sum=self.uy_after_sub_sum_8_8)

        # sub y - u
        self.uy_after_carry1_sub_switch = self.var("uy_after_carry1_sub_switch", 2)
        self.uy_after_sum1_sub_switch = self.var("uy_after_sum1_sub_switch", 2)

        uy_after1_sub_switch = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after1_sub_switch",
                        uy_after1_sub_switch,
                        b_carry=self.u_carry_by_4[1, 0],
                        b_sum=self.u_sum_by_4[1, 0],
                        a_carry=self.y_carry_in[1, 0],
                        a_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry1_sub_switch,
                        final_out_sum=self.uy_after_sum1_sub_switch)

        self.uy_after_carry2_sub_switch = self.var("uy_after_carry2_sub_switch", 2)
        self.uy_after_sum2_sub_switch = self.var("uy_after_sum2_sub_switch", 2)

        uy_after2_sub_switch = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after2_sub_switch",
                        uy_after2_sub_switch,
                        b_carry=self.u_ogb2_by4_carry[1, 0],
                        b_sum=self.u_ogb2_by4_sum[1, 0],
                        a_carry=self.y_carry_in[1, 0],
                        a_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry2_sub_switch,
                        final_out_sum=self.uy_after_sum2_sub_switch)
        
        self.uy_after_carry3_sub_switch = self.var("uy_after_carry3_sub_switch", 2)
        self.uy_after_sum3_sub_switch = self.var("uy_after_sum3_sub_switch", 2)

        uy_after3_sub_switch = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after3_sub_switch",
                        uy_after3_sub_switch,
                        b_carry=self.u_ogb_by4_carry[1, 0],
                        b_sum=self.u_ogb_by4_sum[1, 0],
                        a_carry=self.y_carry_in[1, 0],
                        a_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry3_sub_switch,
                        final_out_sum=self.uy_after_sum3_sub_switch)

        self.uy_after_carry4_sub_switch = self.var("uy_after_carry4_sub_switch", 2)
        self.uy_after_sum4_sub_switch = self.var("uy_after_sum4_sub_switch", 2)

        uy_after4_sub_switch = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after4_sub_switch",
                        uy_after4_sub_switch,
                        b_carry=self.u_ogb3_by4_carry[1, 0],
                        b_sum=self.u_ogb3_by4_sum[1, 0],
                        a_carry=self.y_carry_in[1, 0],
                        a_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry4_sub_switch,
                        final_out_sum=self.uy_after_sum4_sub_switch)
        
        self.uy_after_carry5_sub_switch = self.var("uy_after_carry5_sub_switch", 2)
        self.uy_after_sum5_sub_switch = self.var("uy_after_sum5_sub_switch", 2)

        uy_after5_sub_switch = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after5_sub_switch",
                        uy_after5_sub_switch,
                        b_carry=self.u_ogb_by_2_carry[1, 0],
                        b_sum=self.u_ogb_by_2_sum[1, 0],
                        a_carry=self.y_carry_in[1, 0],
                        a_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry5_sub_switch,
                        final_out_sum=self.uy_after_sum5_sub_switch)
        
        self.uy_after_carry6_sub_switch = self.var("uy_after_carry6_sub_switch", 2)
        self.uy_after_sum6_sub_switch = self.var("uy_after_sum6_sub_switch", 2)

        uy_after6_sub_switch = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after6_sub_switch",
                        uy_after6_sub_switch,
                        b_carry=self.u_carry_by_2[1, 0],
                        b_sum=self.u_sum_by_2[1, 0],
                        a_carry=self.y_carry_in[1, 0],
                        a_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_carry6_sub_switch,
                        final_out_sum=self.uy_after_sum6_sub_switch)

        self.uy_add_after_carry_sub_switch = self.var("uy_add_after_carry_sub_switch", 2)
        self.uy_add_after_sum_sub_switch = self.var("uy_add_after_sum_sub_switch", 2)

        uy_add_after_sub_switch = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_add_after_sub_switch",
                        uy_add_after_sub_switch,
                        a_carry=self.y_carry_in[1, 0],
                        a_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_add_after_carry_sub_switch,
                        final_out_sum=self.uy_add_after_sum_sub_switch)
        
        self.uy_add_after_carry_sub_switch_by_2 = self.var("uy_add_after_carry_sub_switch_by_2", 2)
        self.uy_add_after_sum_sub_switch_by_2 = self.var("uy_add_after_sum_sub_switch_by_2", 2)

        uy_add_after_sub_switch_by_2 = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_add_after_sub_switch_by_2",
                        uy_add_after_sub_switch_by_2,
                        a_carry=self.y_carry_in[1, 0],
                        a_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_add_after_carry_sub_switch_by_2,
                        final_out_sum=self.uy_add_after_sum_sub_switch_by_2)
        
        self.uy_add_after_carry_sub_switch_ogb_by_2 = self.var("uy_add_after_carry_sub_switch_ogb_by_2", 2)
        self.uy_add_after_sum_sub_switch_ogb_by_2 = self.var("uy_add_after_sum_sub_switch_ogb_by_2", 2)

        uy_add_after_sub_switch_ogb_by_2 = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_add_after_sub_switch_ogb_by_2",
                        uy_add_after_sub_switch_ogb_by_2,
                        a_carry=self.y_carry_in[1, 0],
                        a_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_add_after_carry_sub_switch_ogb_by_2,
                        final_out_sum=self.uy_add_after_sum_sub_switch_ogb_by_2)
        
        self.uy_sub_after_carry_sub_switch = self.var("uy_sub_after_carry_sub_switch", 2)
        self.uy_sub_after_sum_sub_switch = self.var("uy_sub_after_sum_sub_switch", 2)

        uy_sub_after_sub_switch = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_sub_after_sub_switch",
                        uy_sub_after_sub_switch,
                        a_carry=self.y_carry_in[1, 0],
                        a_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_sub_after_carry_sub_switch,
                        final_out_sum=self.uy_sub_after_sum_sub_switch)
        
        self.uy_sub_after_carry_sub_by2_switch = self.var("uy_sub_after_carry_sub_by2_switch", 2)
        self.uy_sub_after_sum_sub_by2_switch = self.var("uy_sub_after_sum_sub_by2_switch", 2)

        uy_sub_after_sub_by2_switch = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_sub_after_sub_by2_switch",
                        uy_sub_after_sub_by2_switch,
                        a_carry=self.y_carry_in[1, 0],
                        a_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_sub_after_carry_sub_by2_switch,
                        final_out_sum=self.uy_sub_after_sum_sub_by2_switch)
        
        self.uy_sub_after_carry_sub_ogb_by2_switch = self.var("uy_sub_after_carry_sub_ogb_by2_switch", 2)
        self.uy_sub_after_sum_sub_ogb_by2_switch = self.var("uy_sub_after_sum_sub_ogb_by2_switch", 2)

        uy_sub_after_sub_ogb_by2_switch = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_sub_after_sub_ogb_by2_switch",
                        uy_sub_after_sub_ogb_by2_switch,
                        a_carry=self.y_carry_in[1, 0],
                        a_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_sub_after_carry_sub_ogb_by2_switch,
                        final_out_sum=self.uy_sub_after_sum_sub_ogb_by2_switch)
        
        # wire shared signals between Bezout modules
        if self.u_l:
            self.wire(uy_add_after_sub_switch.ports.b_carry, self.u_delta_update_add_carry[1, 0])
            self.wire(uy_add_after_sub_switch.ports.b_sum, self.u_delta_update_add_sum[1, 0])
            self.wire(uy_add_after_sub_switch_by_2.ports.b_carry, self.u_delta_update_add_carry_by_2[1, 0])
            self.wire(uy_add_after_sub_switch_by_2.ports.b_sum, self.u_delta_update_add_sum_by_2[1, 0])
            self.wire(uy_add_after_sub_switch_ogb_by_2.ports.b_carry, self.u_delta_update_add_ogb_by_2_carry[1, 0])
            self.wire(uy_add_after_sub_switch_ogb_by_2.ports.b_sum, self.u_delta_update_add_ogb_by_2_sum[1, 0])

            self.wire(uy_sub_after_sub_switch.ports.b_carry, self.u_delta_update_sub_first_carry[1, 0])
            self.wire(uy_sub_after_sub_switch.ports.b_sum, self.u_delta_update_sub_first_sum[1, 0])
            self.wire(uy_sub_after_sub_by2_switch.ports.b_carry, self.u_delta_update_sub_first_carry_by_2[1, 0])
            self.wire(uy_sub_after_sub_by2_switch.ports.b_sum, self.u_delta_update_sub_first_sum_by_2[1, 0])
            self.wire(uy_sub_after_sub_ogb_by2_switch.ports.b_carry, self.u_delta_update_sub_first_ogb_by_2_carry[1, 0])
            self.wire(uy_sub_after_sub_ogb_by2_switch.ports.b_sum, self.u_delta_update_sub_first_ogb_by_2_sum[1, 0])
        else:
            self.wire(uy_add_after_sub_switch.ports.b_carry, self.u_delta_update_add_carry_out[1, 0])
            self.wire(uy_add_after_sub_switch.ports.b_sum, self.u_delta_update_add_sum_out[1, 0])
            self.wire(uy_add_after_sub_switch_by_2.ports.b_carry, self.u_delta_update_add_carry_by_2_out[1, 0])
            self.wire(uy_add_after_sub_switch_by_2.ports.b_sum, self.u_delta_update_add_sum_by_2_out[1, 0])
            self.wire(uy_add_after_sub_switch_ogb_by_2.ports.b_carry, self.u_delta_update_add_ogb_by_2_carry_out[1, 0])
            self.wire(uy_add_after_sub_switch_ogb_by_2.ports.b_sum, self.u_delta_update_add_ogb_by_2_sum_out[1, 0])

            self.wire(uy_sub_after_sub_switch.ports.b_carry, self.u_delta_update_sub_first_carry_out[1, 0])
            self.wire(uy_sub_after_sub_switch.ports.b_sum, self.u_delta_update_sub_first_sum_out[1, 0])
            self.wire(uy_sub_after_sub_by2_switch.ports.b_carry, self.u_delta_update_sub_first_carry_by_2_out[1, 0])
            self.wire(uy_sub_after_sub_by2_switch.ports.b_sum, self.u_delta_update_sub_first_sum_by_2_out[1, 0])
            self.wire(uy_sub_after_sub_ogb_by2_switch.ports.b_carry, self.u_delta_update_sub_first_ogb_by_2_carry_out[1, 0])
            self.wire(uy_sub_after_sub_ogb_by2_switch.ports.b_sum, self.u_delta_update_sub_first_ogb_by_2_sum_out[1, 0])

        # divby8 u - y
        self.uy_after_sub_switch_carry_8_1 = self.var("uy_after_sub_switch_carry_8_1", 2)
        self.uy_after_sub_switch_sum_8_1 = self.var("uy_after_sub_switch_sum_8_1", 2)

        uy_after_sub_switch_8_1 = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after_sub_switch_8_1",
                        uy_after_sub_switch_8_1,
                        b_carry=self.u_carry_by_8[1, 0],
                        b_sum=self.u_sum_by_8[1, 0],
                        a_carry=self.y_carry_in[1, 0],
                        a_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_sub_switch_carry_8_1,
                        final_out_sum=self.uy_after_sub_switch_sum_8_1)

        self.uy_after_sub_switch_carry_8_2 = self.var("uy_after_sub_switch_carry_8_2", 2)
        self.uy_after_sub_switch_sum_8_2 = self.var("uy_after_sub_switch_sum_8_2", 2)

        uy_after_sub_switch_8_2 = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after_sub_switch_8_2",
                        uy_after_sub_switch_8_2,
                        b_carry=self.u_ogb4_by_8_carry[1, 0],
                        b_sum=self.u_ogb4_by_8_sum[1, 0],
                        a_carry=self.y_carry_in[1, 0],
                        a_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_sub_switch_carry_8_2,
                        final_out_sum=self.uy_after_sub_switch_sum_8_2)

        self.uy_after_sub_switch_carry_8_3 = self.var("uy_after_sub_switch_carry_8_3", 2)
        self.uy_after_sub_switch_sum_8_3 = self.var("uy_after_sub_switch_sum_8_3", 2)

        uy_after_sub_switch_8_3 = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after_sub_switch_8_3",
                        uy_after_sub_switch_8_3,
                        b_carry=self.u_ogb2_by8_carry[1, 0],
                        b_sum=self.u_ogb2_by8_sum[1, 0],
                        a_carry=self.y_carry_in[1, 0],
                        a_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_sub_switch_carry_8_3,
                        final_out_sum=self.uy_after_sub_switch_sum_8_3)
        
        self.uy_after_sub_switch_carry_8_4 = self.var("uy_after_sub_switch_carry_8_4", 2)
        self.uy_after_sub_switch_sum_8_4 = self.var("uy_after_sub_switch_sum_8_4", 2)

        uy_after_sub_switch_8_4 = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after_sub_switch_8_4",
                        uy_after_sub_switch_8_4,
                        b_carry=self.u_ogb6_by8_carry[1, 0],
                        b_sum=self.u_ogb6_by8_sum[1, 0],
                        a_carry=self.y_carry_in[1, 0],
                        a_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_sub_switch_carry_8_4,
                        final_out_sum=self.uy_after_sub_switch_sum_8_4)

        self.uy_after_sub_switch_carry_8_5 = self.var("uy_after_sub_switch_carry_8_5", 2)
        self.uy_after_sub_switch_sum_8_5 = self.var("uy_after_sub_switch_sum_8_5", 2)

        uy_after_sub_switch_8_5 = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after_sub_switch_8_5",
                        uy_after_sub_switch_8_5,
                        b_carry=self.u_ogb_by8_carry[1, 0],
                        b_sum=self.u_ogb_by8_sum[1, 0],
                        a_carry=self.y_carry_in[1, 0],
                        a_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_sub_switch_carry_8_5,
                        final_out_sum=self.uy_after_sub_switch_sum_8_5)
        
        self.uy_after_sub_switch_carry_8_6 = self.var("uy_after_sub_switch_carry_8_6", 2)
        self.uy_after_sub_switch_sum_8_6 = self.var("uy_after_sub_switch_sum_8_6", 2)

        uy_after_sub_switch_8_6 = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after_sub_switch_8_6",
                        uy_after_sub_switch_8_6,
                        b_carry=self.u_ogb5_by8_carry[1, 0],
                        b_sum=self.u_ogb5_by8_sum[1, 0],
                        a_carry=self.y_carry_in[1, 0],
                        a_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_sub_switch_carry_8_6,
                        final_out_sum=self.uy_after_sub_switch_sum_8_6)
        
        self.uy_after_sub_switch_carry_8_7 = self.var("uy_after_sub_switch_carry_8_7", 2)
        self.uy_after_sub_switch_sum_8_7 = self.var("uy_after_sub_switch_sum_8_7", 2)

        uy_after_sub_switch_8_7 = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after_sub_switch_8_7",
                        uy_after_sub_switch_8_7,
                        b_carry=self.u_ogb3_by8_carry[1, 0],
                        b_sum=self.u_ogb3_by8_sum[1, 0],
                        a_carry=self.y_carry_in[1, 0],
                        a_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_sub_switch_carry_8_7,
                        final_out_sum=self.uy_after_sub_switch_sum_8_7)
        
        self.uy_after_sub_switch_carry_8_8 = self.var("uy_after_sub_switch_carry_8_8", 2)
        self.uy_after_sub_switch_sum_8_8 = self.var("uy_after_sub_switch_sum_8_8", 2)

        uy_after_sub_switch_8_8 = DW01_csa_4(2, False, DW=self.DW)
        self.add_child("uy_after_sub_switch_8_8",
                        uy_after_sub_switch_8_8,
                        b_carry=self.u_ogb7_by8_carry[1, 0],
                        b_sum=self.u_ogb7_by8_sum[1, 0],
                        a_carry=self.y_carry_in[1, 0],
                        a_sum=self.y_sum_in[1, 0],
                        final_out_carry=self.uy_after_sub_switch_carry_8_8,
                        final_out_sum=self.uy_after_sub_switch_sum_8_8)

        # u + y + ogb lsb 2
        self.uyb_after_carry1 = self.var("uyb_after_carry1", 2)
        self.uyb_after_sum1 = self.var("uyb_after_sum1", 2)

        csa_u_y_ogb_1 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_1.width.value = 2
        self.add_child("csa_u_y_ogb_1", 
                       csa_u_y_ogb_1,
                       a=self.uy_after_carry1,
                       b=self.uy_after_sum1,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry1,
                       sum=self.uyb_after_sum1)

        self.uyb_after_carry2 = self.var("uyb_after_carry2", 2)
        self.uyb_after_sum2 = self.var("uyb_after_sum2", 2)

        csa_u_y_ogb_2 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_2.width.value = 2
        self.add_child("csa_u_y_ogb_2", 
                       csa_u_y_ogb_2,
                       a=self.uy_after_carry2,
                       b=self.uy_after_sum2,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry2,
                       sum=self.uyb_after_sum2)
        
        self.uyb_after_carry3 = self.var("uyb_after_carry3", 2)
        self.uyb_after_sum3 = self.var("uyb_after_sum3", 2)

        csa_u_y_ogb_3 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_3.width.value = 2
        self.add_child("csa_u_y_ogb_3", 
                       csa_u_y_ogb_3,
                       a=self.uy_after_carry3,
                       b=self.uy_after_sum3,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry3,
                       sum=self.uyb_after_sum3)
        
        self.uyb_after_carry4 = self.var("uyb_after_carry4", 2)
        self.uyb_after_sum4 = self.var("uyb_after_sum4", 2)

        csa_u_y_ogb_4 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_4.width.value = 2
        self.add_child("csa_u_y_ogb_4", 
                       csa_u_y_ogb_4,
                       a=self.uy_after_carry4,
                       b=self.uy_after_sum4,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry4,
                       sum=self.uyb_after_sum4)
    
        self.uyb_after_carry5 = self.var("uyb_after_carry5", 2)
        self.uyb_after_sum5 = self.var("uyb_after_sum5", 2)

        csa_u_y_ogb_5 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_5.width.value = 2
        self.add_child("csa_u_y_ogb_5", 
                       csa_u_y_ogb_5,
                       a=self.uy_after_carry5,
                       b=self.uy_after_sum5,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry5,
                       sum=self.uyb_after_sum5)

        self.uyb_after_carry6 = self.var("uyb_after_carry6", 2)
        self.uyb_after_sum6 = self.var("uyb_after_sum6", 2)

        csa_u_y_ogb_6 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_6.width.value = 2
        self.add_child("csa_u_y_ogb_6", 
                       csa_u_y_ogb_6,
                       a=self.uy_after_carry6,
                       b=self.uy_after_sum6,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry6,
                       sum=self.uyb_after_sum6)
        
        self.uyb_after_carryadd = self.var("uyb_after_carryadd", 2)
        self.uyb_after_sumadd = self.var("uyb_after_sumadd", 2)

        csa_u_y_ogb_add = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_add.width.value = 2
        self.add_child("csa_u_y_ogb_add", 
                       csa_u_y_ogb_add,
                       a=self.uy_add_after_carry,
                       b=self.uy_add_after_sum,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carryadd,
                       sum=self.uyb_after_sumadd)
        
        self.uyb_after_carrysub = self.var("uyb_after_carrysub", 2)
        self.uyb_after_sumsub = self.var("uyb_after_sumsub", 2)

        csa_u_y_ogb_sub = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_sub.width.value = 2
        self.add_child("csa_u_y_ogb_sub", 
                       csa_u_y_ogb_sub,
                       a=self.uy_sub_after_carry,
                       b=self.uy_sub_after_sum,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carrysub,
                       sum=self.uyb_after_sumsub)
        
        self.uyb_after_carry_by_2_add = self.var("uyb_after_carry_by_2_add", 2)
        self.uyb_after_sum_by_2_add = self.var("uyb_after_sum_by_2_add", 2)

        csa_u_y_ogb_by_2_add = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_by_2_add.width.value = 2
        self.add_child("csa_u_y_ogb_by_2_add", 
                       csa_u_y_ogb_by_2_add,
                       a=self.uy_add_after_by_2_carry,
                       b=self.uy_add_after_by_2_sum,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry_by_2_add,
                       sum=self.uyb_after_sum_by_2_add)
        
        self.uyb_after_carry_by_2_sub = self.var("uyb_after_carry_by_2_sub", 2)
        self.uyb_after_sum_by_2_sub = self.var("uyb_after_sum_by_2_sub", 2)

        csa_u_y_ogb_by_2_sub = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_by_2_sub.width.value = 2
        self.add_child("csa_u_y_ogb_by_2_sub", 
                       csa_u_y_ogb_by_2_sub,
                       a=self.uy_sub_after_by_2_carry,
                       b=self.uy_sub_after_by_2_sum,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry_by_2_sub,
                       sum=self.uyb_after_sum_by_2_sub)

        self.uyb_after_carry_ogb_by_2_add = self.var("uyb_after_carry_ogb_by_2_add", 2)
        self.uyb_after_sum_ogb_by_2_add = self.var("uyb_after_sum_ogb_by_2_add", 2)

        csa_u_y_ogb_ogb_by_2_add = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_ogb_by_2_add.width.value = 2
        self.add_child("csa_u_y_ogb_ogb_by_2_add", 
                       csa_u_y_ogb_ogb_by_2_add,
                       a=self.uy_add_after_ogb_by_2_carry,
                       b=self.uy_add_after_ogb_by_2_sum,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry_ogb_by_2_add,
                       sum=self.uyb_after_sum_ogb_by_2_add)
        
        self.uyb_after_carry_ogb_by_2_sub = self.var("uyb_after_carry_ogb_by_2_sub", 2)
        self.uyb_after_sum_ogb_by_2_sub = self.var("uyb_after_sum_ogb_by_2_sub", 2)

        csa_u_y_ogb_ogb_by_2_sub = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_ogb_by_2_sub.width.value = 2
        self.add_child("csa_u_y_ogb_ogb_by_2_sub", 
                       csa_u_y_ogb_ogb_by_2_sub,
                       a=self.uy_sub_after_ogb_by_2_carry,
                       b=self.uy_sub_after_ogb_by_2_sum,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry_ogb_by_2_sub,
                       sum=self.uyb_after_sum_ogb_by_2_sub)

        # divby8 u + y + og_b lsb_2
        self.uyb_8_after_carry1 = self.var("uyb_8_after_carry1", 2)
        self.uyb_8_after_sum1 = self.var("uyb_8_after_sum1", 2)

        csa_u_y_ogb_8_1 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_8_1.width.value = 2
        self.add_child("csa_u_y_ogb_8_1", 
                       csa_u_y_ogb_8_1,
                       a=self.uy_after_carry_8_1,
                       b=self.uy_after_sum_8_1,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_8_after_carry1,
                       sum=self.uyb_8_after_sum1)
        
        self.uyb_8_after_carry2 = self.var("uyb_8_after_carry2", 2)
        self.uyb_8_after_sum2 = self.var("uyb_8_after_sum2", 2)

        csa_u_y_ogb_8_2 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_8_2.width.value = 2
        self.add_child("csa_u_y_ogb_8_2", 
                       csa_u_y_ogb_8_2,
                       a=self.uy_after_carry_8_2,
                       b=self.uy_after_sum_8_2,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_8_after_carry2,
                       sum=self.uyb_8_after_sum2)
        
        self.uyb_8_after_carry3 = self.var("uyb_8_after_carry3", 2)
        self.uyb_8_after_sum3 = self.var("uyb_8_after_sum3", 2)

        csa_u_y_ogb_8_3 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_8_3.width.value = 2
        self.add_child("csa_u_y_ogb_8_3", 
                       csa_u_y_ogb_8_3,
                       a=self.uy_after_carry_8_3,
                       b=self.uy_after_sum_8_3,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_8_after_carry3,
                       sum=self.uyb_8_after_sum3)
        
        self.uyb_8_after_carry4 = self.var("uyb_8_after_carry4", 2)
        self.uyb_8_after_sum4 = self.var("uyb_8_after_sum4", 2)

        csa_u_y_ogb_8_4 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_8_4.width.value = 2
        self.add_child("csa_u_y_ogb_8_4", 
                       csa_u_y_ogb_8_4,
                       a=self.uy_after_carry_8_4,
                       b=self.uy_after_sum_8_4,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_8_after_carry4,
                       sum=self.uyb_8_after_sum4)
    
        self.uyb_8_after_carry5 = self.var("uyb_8_after_carry5", 2)
        self.uyb_8_after_sum5 = self.var("uyb_8_after_sum5", 2)

        csa_u_y_ogb_8_5 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_8_5.width.value = 2
        self.add_child("csa_u_y_ogb_8_5", 
                       csa_u_y_ogb_8_5,
                       a=self.uy_after_carry_8_5,
                       b=self.uy_after_sum_8_5,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_8_after_carry5,
                       sum=self.uyb_8_after_sum5)

        self.uyb_8_after_carry6 = self.var("uyb_8_after_carry6", 2)
        self.uyb_8_after_sum6 = self.var("uyb_8_after_sum6", 2)

        csa_u_y_ogb_8_6 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_8_6.width.value = 2
        self.add_child("csa_u_y_ogb_8_6", 
                       csa_u_y_ogb_8_6,
                       a=self.uy_after_carry_8_6,
                       b=self.uy_after_sum_8_6,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_8_after_carry6,
                       sum=self.uyb_8_after_sum6)
        
        self.uyb_8_after_carry7 = self.var("uyb_8_after_carry7", 2)
        self.uyb_8_after_sum7 = self.var("uyb_8_after_sum7", 2)

        csa_u_y_ogb_8_add = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_8_add.width.value = 2
        self.add_child("csa_u_y_ogb_8_add", 
                       csa_u_y_ogb_8_add,
                       a=self.uy_after_carry_8_7,
                       b=self.uy_after_sum_8_7,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_8_after_carry7,
                       sum=self.uyb_8_after_sum7)
        
        self.uyb_8_after_carry8 = self.var("uyb_8_after_carry8", 2)
        self.uyb_8_after_sum8 = self.var("uyb_8_after_sum8", 2)

        csa_u_y_ogb_8_sub = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_8_sub.width.value = 2
        self.add_child("csa_u_y_ogb_8_sub", 
                       csa_u_y_ogb_8_sub,
                       a=self.uy_after_carry_8_8,
                       b=self.uy_after_sum_8_8,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_8_after_carry8,
                       sum=self.uyb_8_after_sum8)

        # u - y + ogb lsb 2
        self.uyb_after_carry1_sub = self.var("uyb_after_carry1_sub", 2)
        self.uyb_after_sum1_sub = self.var("uyb_after_sum1_sub", 2)

        csa_u_y_ogb_1_sub = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_1_sub.width.value = 2
        self.add_child("csa_u_y_ogb_1_sub", 
                       csa_u_y_ogb_1_sub,
                       a=self.uy_after_carry1_sub,
                       b=self.uy_after_sum1_sub,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry1_sub,
                       sum=self.uyb_after_sum1_sub)
        
        self.uyb_after_carry2_sub = self.var("uyb_after_carry2_sub", 2)
        self.uyb_after_sum2_sub = self.var("uyb_after_sum2_sub", 2)

        csa_u_y_ogb_2_sub = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_2_sub.width.value = 2
        self.add_child("csa_u_y_ogb_2_sub", 
                       csa_u_y_ogb_2_sub,
                       a=self.uy_after_carry2_sub,
                       b=self.uy_after_sum2_sub,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry2_sub,
                       sum=self.uyb_after_sum2_sub)
        
        self.uyb_after_carry3_sub = self.var("uyb_after_carry3_sub", 2)
        self.uyb_after_sum3_sub = self.var("uyb_after_sum3_sub", 2)

        csa_u_y_ogb_3_sub = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_3_sub.width.value = 2
        self.add_child("csa_u_y_ogb_3_sub", 
                       csa_u_y_ogb_3_sub,
                       a=self.uy_after_carry3_sub,
                       b=self.uy_after_sum3_sub,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry3_sub,
                       sum=self.uyb_after_sum3_sub)
        
        self.uyb_after_carry4_sub = self.var("uyb_after_carry4_sub", 2)
        self.uyb_after_sum4_sub = self.var("uyb_after_sum4_sub", 2)

        csa_u_y_ogb_4_sub = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_4_sub.width.value = 2
        self.add_child("csa_u_y_ogb_4_sub", 
                       csa_u_y_ogb_4_sub,
                       a=self.uy_after_carry4_sub,
                       b=self.uy_after_sum4_sub,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry4_sub,
                       sum=self.uyb_after_sum4_sub)
    
        self.uyb_after_carry5_sub = self.var("uyb_after_carry5_sub", 2)
        self.uyb_after_sum5_sub = self.var("uyb_after_sum5_sub", 2)

        csa_u_y_ogb_5_sub = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_5_sub.width.value = 2
        self.add_child("csa_u_y_ogb_5_sub", 
                       csa_u_y_ogb_5_sub,
                       a=self.uy_after_carry5_sub,
                       b=self.uy_after_sum5_sub,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry5_sub,
                       sum=self.uyb_after_sum5_sub)

        self.uyb_after_carry6_sub = self.var("uyb_after_carry6_sub", 2)
        self.uyb_after_sum6_sub = self.var("uyb_after_sum6_sub", 2)

        csa_u_y_ogb_6_sub = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_6_sub.width.value = 2
        self.add_child("csa_u_y_ogb_6_sub", 
                       csa_u_y_ogb_6_sub,
                       a=self.uy_after_carry6_sub,
                       b=self.uy_after_sum6_sub,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry6_sub,
                       sum=self.uyb_after_sum6_sub)
        
        self.uyb_after_carryadd_sub = self.var("uyb_after_carryadd_sub", 2)
        self.uyb_after_sumadd_sub = self.var("uyb_after_sumadd_sub", 2)

        csa_u_y_ogb_add_sub = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_add_sub.width.value = 2
        self.add_child("csa_u_y_ogb_add_sub", 
                       csa_u_y_ogb_add_sub,
                       a=self.uy_add_after_carry_sub,
                       b=self.uy_add_after_sum_sub,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carryadd_sub,
                       sum=self.uyb_after_sumadd_sub)
        
        self.uyb_after_carrysub_sub = self.var("uyb_after_carrysub_sub", 2)
        self.uyb_after_sumsub_sub = self.var("uyb_after_sumsub_sub", 2)

        csa_u_y_ogb_sub_sub = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_sub_sub.width.value = 2
        self.add_child("csa_u_y_ogb_sub_sub", 
                       csa_u_y_ogb_sub_sub,
                       a=self.uy_sub_after_carry_sub,
                       b=self.uy_sub_after_sum_sub,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carrysub_sub,
                       sum=self.uyb_after_sumsub_sub)
        
        self.uyb_after_carry_by_2_add_sub = self.var("uyb_after_carry_by_2_add_sub", 2)
        self.uyb_after_sum_by_2_add_sub = self.var("uyb_after_sum_by_2_add_sub", 2)

        csa_u_y_ogb_add_sub_by_2 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_add_sub_by_2.width.value = 2
        self.add_child("csa_u_y_ogb_add_sub_by_2", 
                       csa_u_y_ogb_add_sub_by_2,
                       a=self.uy_add_after_by_2_carry_sub,
                       b=self.uy_add_after_by_2_sum_sub,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry_by_2_add_sub,
                       sum=self.uyb_after_sum_by_2_add_sub)
        
        self.uyb_after_carry_by_2_sub_sub = self.var("uyb_after_carry_by_2_sub_sub", 2)
        self.uyb_after_sum_by_2_sub_sub = self.var("uyb_after_sum_by_2_sub_sub", 2)

        csa_u_y_ogb_sub_sub_by_2 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_sub_sub_by_2.width.value = 2
        self.add_child("csa_u_y_ogb_sub_sub_by_2", 
                       csa_u_y_ogb_sub_sub_by_2,
                       a=self.uy_sub_after_by_2_carry_sub,
                       b=self.uy_sub_after_by_2_sum_sub,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry_by_2_sub_sub,
                       sum=self.uyb_after_sum_by_2_sub_sub)
        
        self.uyb_after_carry_ogb_by_2_add_sub = self.var("uyb_after_carry_ogb_by_2_add_sub", 2)
        self.uyb_after_sum_ogb_by_2_add_sub = self.var("uyb_after_sum_ogb_by_2_add_sub", 2)

        csa_u_y_ogb_add_sub_ogb_by_2 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_add_sub_ogb_by_2.width.value = 2
        self.add_child("csa_u_y_ogb_add_sub_ogb_by_2", 
                       csa_u_y_ogb_add_sub_ogb_by_2,
                       a=self.uy_add_after_ogb_by_2_carry_sub,
                       b=self.uy_add_after_ogb_by_2_sum_sub,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry_ogb_by_2_add_sub,
                       sum=self.uyb_after_sum_ogb_by_2_add_sub)
        
        self.uyb_after_carry_ogb_by_2_sub_sub = self.var("uyb_after_carry_ogb_by_2_sub_sub", 2)
        self.uyb_after_sum_ogb_by_2_sub_sub = self.var("uyb_after_sum_ogb_by_2_sub_sub", 2)

        csa_u_y_ogb_sub_sub_ogb_by_2 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_sub_sub_ogb_by_2.width.value = 2
        self.add_child("csa_u_y_ogb_sub_sub_ogb_by_2", 
                       csa_u_y_ogb_sub_sub_ogb_by_2,
                       a=self.uy_sub_after_ogb_by_2_carry_sub,
                       b=self.uy_sub_after_ogb_by_2_sum_sub,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry_ogb_by_2_sub_sub,
                       sum=self.uyb_after_sum_ogb_by_2_sub_sub)
        
        # divby8 u - y + og_b lsb_2
        self.uyb_8_after_sub_carry1 = self.var("uyb_8_after_sub_carry1", 2)
        self.uyb_8_after_sub_sum1 = self.var("uyb_8_after_sub_sum1", 2)

        csa_u_y_ogb_sub_8_1 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_sub_8_1.width.value = 2
        self.add_child("csa_u_y_ogb_sub_8_1", 
                       csa_u_y_ogb_sub_8_1,
                       a=self.uy_after_carry_8_1,
                       b=self.uy_after_sum_8_1,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_8_after_sub_carry1,
                       sum=self.uyb_8_after_sub_sum1)
        
        self.uyb_8_after_sub_carry2 = self.var("uyb_8_after_sub_carry2", 2)
        self.uyb_8_after_sub_sum2 = self.var("uyb_8_after_sub_sum2", 2)

        csa_u_y_ogb_sub_8_2 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_sub_8_2.width.value = 2
        self.add_child("csa_u_y_ogb_sub_8_2", 
                       csa_u_y_ogb_sub_8_2,
                       a=self.uy_after_carry_8_2,
                       b=self.uy_after_sum_8_2,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_8_after_sub_carry2,
                       sum=self.uyb_8_after_sub_sum2)
        
        self.uyb_8_after_sub_carry3 = self.var("uyb_8_after_sub_carry3", 2)
        self.uyb_8_after_sub_sum3 = self.var("uyb_8_after_sub_sum3", 2)

        csa_u_y_ogb_sub_8_3 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_sub_8_3.width.value = 2
        self.add_child("csa_u_y_ogb_sub_8_3", 
                       csa_u_y_ogb_sub_8_3,
                       a=self.uy_after_carry_8_3,
                       b=self.uy_after_sum_8_3,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_8_after_sub_carry3,
                       sum=self.uyb_8_after_sub_sum3)
        
        self.uyb_8_after_sub_carry4 = self.var("uyb_8_after_sub_carry4", 2)
        self.uyb_8_after_sub_sum4 = self.var("uyb_8_after_sub_sum4", 2)

        csa_u_y_ogb_sub_8_4 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_sub_8_4.width.value = 2
        self.add_child("csa_u_y_ogb_sub_8_4", 
                       csa_u_y_ogb_sub_8_4,
                       a=self.uy_after_carry_8_4,
                       b=self.uy_after_sum_8_4,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_8_after_sub_carry4,
                       sum=self.uyb_8_after_sub_sum4)
    
        self.uyb_8_after_sub_carry5 = self.var("uyb_8_after_sub_carry5", 2)
        self.uyb_8_after_sub_sum5 = self.var("uyb_8_after_sub_sum5", 2)

        csa_u_y_ogb_sub_8_5 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_sub_8_5.width.value = 2
        self.add_child("csa_u_y_ogb_sub_8_5", 
                       csa_u_y_ogb_sub_8_5,
                       a=self.uy_after_carry_8_5,
                       b=self.uy_after_sum_8_5,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_8_after_sub_carry5,
                       sum=self.uyb_8_after_sub_sum5)

        self.uyb_8_after_sub_carry6 = self.var("uyb_8_after_sub_carry6", 2)
        self.uyb_8_after_sub_sum6 = self.var("uyb_8_after_sub_sum6", 2)

        csa_u_y_ogb_sub_8_6 = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_sub_8_6.width.value = 2
        self.add_child("csa_u_y_ogb_sub_8_6", 
                       csa_u_y_ogb_sub_8_6,
                       a=self.uy_after_carry_8_6,
                       b=self.uy_after_sum_8_6,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_8_after_sub_carry6,
                       sum=self.uyb_8_after_sub_sum6)
        
        self.uyb_8_after_sub_carry7 = self.var("uyb_8_after_sub_carry7", 2)
        self.uyb_8_after_sub_sum7 = self.var("uyb_8_after_sub_sum7", 2)

        csa_u_y_ogb_sub_8_add = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_sub_8_add.width.value = 2
        self.add_child("csa_u_y_ogb_sub_8_add", 
                       csa_u_y_ogb_sub_8_add,
                       a=self.uy_after_carry_8_7,
                       b=self.uy_after_sum_8_7,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_8_after_sub_carry7,
                       sum=self.uyb_8_after_sub_sum7)
        
        self.uyb_8_after_sub_carry8 = self.var("uyb_8_after_sub_carry8", 2)
        self.uyb_8_after_sub_sum8 = self.var("uyb_8_after_sub_sum8", 2)

        csa_u_y_ogb_sub_8_sub = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_sub_8_sub.width.value = 2
        self.add_child("csa_u_y_ogb_sub_8_sub", 
                       csa_u_y_ogb_sub_8_sub,
                       a=self.uy_after_carry_8_8,
                       b=self.uy_after_sum_8_8,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_8_after_sub_carry8,
                       sum=self.uyb_8_after_sub_sum8)
        
        # u - y + ogb lsb 2
        self.uyb_after_carry1_sub_switch = self.var("uyb_after_carry1_sub_switch", 2)
        self.uyb_after_sum1_sub_switch = self.var("uyb_after_sum1_sub_switch", 2)

        csa_u_y_ogb_1_sub_switch = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_1_sub_switch.width.value = 2
        self.add_child("csa_u_y_ogb_1_sub_switch", 
                       csa_u_y_ogb_1_sub_switch,
                       a=self.uy_after_carry1_sub_switch,
                       b=self.uy_after_sum1_sub_switch,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry1_sub_switch,
                       sum=self.uyb_after_sum1_sub_switch)
        
        self.uyb_after_carry2_sub_switch = self.var("uyb_after_carry2_sub_switch", 2)
        self.uyb_after_sum2_sub_switch = self.var("uyb_after_sum2_sub_switch", 2)

        csa_u_y_ogb_2_sub_switch = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_2_sub_switch.width.value = 2
        self.add_child("csa_u_y_ogb_2_sub_switch", 
                       csa_u_y_ogb_2_sub_switch,
                       a=self.uy_after_carry2_sub_switch,
                       b=self.uy_after_sum2_sub_switch,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry2_sub_switch,
                       sum=self.uyb_after_sum2_sub_switch)
        
        self.uyb_after_carry3_sub_switch = self.var("uyb_after_carry3_sub_switch", 2)
        self.uyb_after_sum3_sub_switch = self.var("uyb_after_sum3_sub_switch", 2)

        csa_u_y_ogb_3_sub_switch = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_3_sub_switch.width.value = 2
        self.add_child("csa_u_y_ogb_3_sub_switch", 
                       csa_u_y_ogb_3_sub_switch,
                       a=self.uy_after_carry3_sub_switch,
                       b=self.uy_after_sum3_sub_switch,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry3_sub_switch,
                       sum=self.uyb_after_sum3_sub_switch)
        
        self.uyb_after_carry4_sub_switch = self.var("uyb_after_carry4_sub_switch", 2)
        self.uyb_after_sum4_sub_switch = self.var("uyb_after_sum4_sub_switch", 2)

        csa_u_y_ogb_4_sub_switch = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_4_sub_switch.width.value = 2
        self.add_child("csa_u_y_ogb_4_sub_switch", 
                       csa_u_y_ogb_4_sub_switch,
                       a=self.uy_after_carry4_sub_switch,
                       b=self.uy_after_sum4_sub_switch,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry4_sub_switch,
                       sum=self.uyb_after_sum4_sub_switch)
    
        self.uyb_after_carry5_sub_switch = self.var("uyb_after_carry5_sub_switch", 2)
        self.uyb_after_sum5_sub_switch = self.var("uyb_after_sum5_sub_switch", 2)

        csa_u_y_ogb_5_sub_switch = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_5_sub_switch.width.value = 2
        self.add_child("csa_u_y_ogb_5_sub_switch", 
                       csa_u_y_ogb_5_sub_switch,
                       a=self.uy_after_carry5_sub_switch,
                       b=self.uy_after_sum5_sub_switch,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry5_sub_switch,
                       sum=self.uyb_after_sum5_sub_switch)

        self.uyb_after_carry6_sub_switch = self.var("uyb_after_carry6_sub_switch", 2)
        self.uyb_after_sum6_sub_switch = self.var("uyb_after_sum6_sub_switch", 2)

        csa_u_y_ogb_6_sub_switch = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_6_sub_switch.width.value = 2
        self.add_child("csa_u_y_ogb_6_sub_switch", 
                       csa_u_y_ogb_6_sub_switch,
                       a=self.uy_after_carry6_sub_switch,
                       b=self.uy_after_sum6_sub_switch,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carry6_sub_switch,
                       sum=self.uyb_after_sum6_sub_switch)
        
        self.uyb_after_carryadd_sub_switch = self.var("uyb_after_carryadd_sub_switch", 2)
        self.uyb_after_sumadd_sub_switch = self.var("uyb_after_sumadd_sub_switch", 2)

        csa_u_y_ogb_add_sub_switch = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_add_sub_switch.width.value = 2
        self.add_child("csa_u_y_ogb_add_sub_switch", 
                       csa_u_y_ogb_add_sub_switch,
                       a=self.uy_add_after_carry_sub_switch,
                       b=self.uy_add_after_sum_sub_switch,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carryadd_sub_switch,
                       sum=self.uyb_after_sumadd_sub_switch)
        
        self.uyb_after_carrysub_sub_switch = self.var("uyb_after_carrysub_sub_switch", 2)
        self.uyb_after_sumsub_sub_switch = self.var("uyb_after_sumsub_sub_switch", 2)

        csa_u_y_ogb_sub_sub_switch = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_sub_sub_switch.width.value = 2
        self.add_child("csa_u_y_ogb_sub_sub_switch", 
                       csa_u_y_ogb_sub_sub_switch,
                       a=self.uy_sub_after_carry_sub_switch,
                       b=self.uy_sub_after_sum_sub_switch,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carrysub_sub_switch,
                       sum=self.uyb_after_sumsub_sub_switch)
        
        self.uyb_after_carryadd_sub_by_2_switch = self.var("uyb_after_carryadd_sub_by_2_switch", 2)
        self.uyb_after_sumadd_sub_by_2_switch = self.var("uyb_after_sumadd_sub_by_2_switch", 2)

        csa_u_y_ogb_add_sub_by_2_switch = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_add_sub_by_2_switch.width.value = 2
        self.add_child("csa_u_y_ogb_add_sub_by_2_switch", 
                       csa_u_y_ogb_add_sub_by_2_switch,
                       a=self.uy_add_after_carry_sub_switch_by_2,
                       b=self.uy_add_after_sum_sub_switch_by_2,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carryadd_sub_by_2_switch,
                       sum=self.uyb_after_sumadd_sub_by_2_switch)

        self.uyb_after_carrysub_sub_by_2_switch = self.var("uyb_after_carrysub_sub_by_2_switch", 2)
        self.uyb_after_sumsub_sub_by_2_switch = self.var("uyb_after_sumsub_sub_by_2_switch", 2)

        csa_u_y_ogb_sub_sub_by_2_switch = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_sub_sub_by_2_switch.width.value = 2
        self.add_child("csa_u_y_ogb_sub_sub_by_2_switch", 
                       csa_u_y_ogb_sub_sub_by_2_switch,
                       a=self.uy_sub_after_carry_sub_by2_switch,
                       b=self.uy_sub_after_sum_sub_by2_switch,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carrysub_sub_by_2_switch,
                       sum=self.uyb_after_sumsub_sub_by_2_switch)
        
        self.uyb_after_carryadd_sub_ogb_by_2_switch = self.var("uyb_after_carryadd_sub_ogb_by_2_switch", 2)
        self.uyb_after_sumadd_sub_ogb_by_2_switch = self.var("uyb_after_sumadd_sub_ogb_by_2_switch", 2)

        csa_u_y_ogb_add_sub_ogb_by_2_switch = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_add_sub_ogb_by_2_switch.width.value = 2
        self.add_child("csa_u_y_ogb_add_sub_ogb_by_2_switch", 
                       csa_u_y_ogb_add_sub_ogb_by_2_switch,
                       a=self.uy_add_after_carry_sub_switch_ogb_by_2,
                       b=self.uy_add_after_sum_sub_switch_ogb_by_2,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carryadd_sub_ogb_by_2_switch,
                       sum=self.uyb_after_sumadd_sub_ogb_by_2_switch)
        
        self.uyb_after_carrysub_sub_ogb_by_2_switch = self.var("uyb_after_carrysub_sub_ogb_by_2_switch", 2)
        self.uyb_after_sumsub_sub_ogb_by_2_switch = self.var("uyb_after_sumsub_sub_ogb_by_2_switch", 2)

        csa_u_y_ogb_sub_sub_ogb_by_2_switch = DW01_csa(2, DW=self.DW)
        csa_u_y_ogb_sub_sub_ogb_by_2_switch.width.value = 2
        self.add_child("csa_u_y_ogb_sub_sub_ogb_by_2_switch", 
                       csa_u_y_ogb_sub_sub_ogb_by_2_switch,
                       a=self.uy_sub_after_carry_sub_ogb_by2_switch,
                       b=self.uy_sub_after_sum_sub_ogb_by2_switch,
                       c=self.og_b_csa[1, 0],
                       ci=self.ci,
                       carry=self.uyb_after_carrysub_sub_ogb_by_2_switch,
                       sum=self.uyb_after_sumsub_sub_ogb_by_2_switch)

        self.inv_u_ogb2_lsb_3 = self.var("inv_u_ogb2_lsb_3", 1)
        self.wire(self.inv_u_ogb2_lsb_3, ~((self.u_ogb2_carry[1] | self.u_ogb2_sum[1]) ^ self.u_ogb2_carry[2] ^ self.u_ogb2_sum[2]))
        self.inv_u_ogb3_lsb_3 = self.var("inv_u_ogb3_lsb_3", 1)
        self.wire(self.inv_u_ogb3_lsb_3, ~((self.u_ogb3_carry[1] | self.u_ogb3_sum[1]) ^ self.u_ogb3_carry[2] ^ self.u_ogb3_sum[2]))

        # add code blocks
        self.add_code(self.set_u)

        if self.u_y:
            self.add_code(self.set_u_after_lsbs)

        if self.add_og_val:
            self.add_code(self.set_inv_u_ogb_after_lsb_2_add)
            self.add_code(self.set_inv_u_y_ogb_after_lsb_2_add)
        else:
            self.add_code(self.set_inv_u_ogb_after_lsb_2_sub)
            self.add_code(self.set_inv_u_y_ogb_after_lsb_2_sub)
            
        self.add_code(self.set_u_y_after_lsbs)
        self.add_code(self.set_inv_u_ogb_after_lsb_3)

        if self.debug_print:
            self.debug_case = self.var("debug_case", 20)
            self.add_code(self.set_debug_case)

    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def set_u(self):
        if ~self.rst_n:
            self.u_carry = 0
            self.u_sum = 0
            
        elif self.start:

            if self.initial_0:
                self.u_sum = 0
            else:
                self.u_sum = 1
            
            self.u_carry = 0

        elif ~self.done:
            # a even
            if ~self.a_lsb:

                # a divisible by 4
                if self.shift_a_4 & ~self.a_lsb_2:

                    # a divisble by 8 so reduce 3 factors of 2
                    if self.shift_a_8 & ~self.a_lsb_3:

                        # u divisible by 8
                        if ~self.u_after_lsb_3 & ~self.u_after_lsb_2 & ~self.u_after_lsb:
                            # self.u = concat(self.u[self.bit_length_msb], self.u[self.bit_length_msb], self.u[self.bit_length_msb], self.u[self.bit_length_msb, 3])
                            self.u_carry = self.u_carry_by_8
                            self.u_sum = self.u_sum_by_8
                        # u divisible by 4: add og_b to u / 4, divide by 2
                        elif ~self.u_after_lsb_2 & ~self.u_after_lsb:
                            # self.u = concat(self.uby4_ogb[self.bit_length_msb], self.uby4_ogb[self.bit_length_msb, 1])
                            self.u_carry = self.u_ogb4_by_8_carry
                            self.u_sum = self.u_ogb4_by_8_sum
                        # u divisible by 2
                        elif ~self.u_after_lsb:
                            # u / 2 + og_b divisible by 4: add og_b to u / 2, divide by 4
                            # u / 2 must be odd since u is not divisible by 4 (or 8), 
                            # so u / 2 + og_b is guaranteed to be even (do not have to check last bit)
                            # same as checking whether u + 2 * og_b is divisible by 8
                            # if ~self.uby_2_ogb[1]:
                            if self.inv_u_ogb2_lsb_3:
                                # self.u = concat(self.uby_2_ogb[self.bit_length_msb], self.uby_2_ogb[self.bit_length_msb], self.uby_2_ogb[self.bit_length_msb, 2])
                                self.u_carry = self.u_ogb2_by8_carry
                                self.u_sum = self.u_ogb2_by8_sum
                            # u / 2 + og_b guaranteed to be divisible by 2: 
                            # add og_b to u / 2, divide by 2, add og_b to (u / 2 + og_b) / 2, divide by 2
                            # elif ~self.uby_2_ogb[0]:
                            else:
                                # self.u = concat(self.uby_2_ogb_by_2_ogb[self.bit_length_msb], self.uby_2_ogb_by_2_ogb[self.bit_length_msb, 1])
                                self.u_carry = self.u_ogb6_by8_carry
                                self.u_sum = self.u_ogb6_by8_sum
                        # u odd
                        else:
                            # u + og_b divisible by 8: divide by 8
                            # u is odd, so u + og_b will be even (don't have to check last bit)
                            if self.inv_u_ogb_after_lsb_3 & self.inv_u_ogb_after_lsb_2:
                                # self.u = concat(self.u_ogb[self.bit_length_msb], self.u_ogb[self.bit_length_msb], self.u_ogb[self.bit_length_msb], self.u_ogb[self.bit_length_msb, 3])
                                self.u_carry = self.u_ogb_by8_carry
                                self.u_sum = self.u_ogb_by8_sum
                            # u + og_b divisible by 4: divide by 4, add og_b to (u + og_b) / 4, divide by 2
                            elif self.inv_u_ogb_after_lsb_2:
                                # self.u = concat(self.u_ogb_by4_ogb[self.bit_length_msb], self.u_ogb_by4_ogb[self.bit_length_msb, 1])
                                self.u_carry = self.u_ogb5_by8_carry
                                self.u_sum = self.u_ogb5_by8_sum
                            # u + og_b guaranteed to be divisble by 2
                            # elif ~self.u_ogb[0]:
                            else:
                                # (u + og_b) / 2 + og_b is divisible by 4
                                # will be divisible by 2 by definition since odd ((u + og_b) / 2) + odd (og_b) = even

                                # (u + og_b) // 2 + og_b = (u + 3 * og_b) // 2
                                # want to check if (u + 3 * og_b) is divisible by 8 (whether (u + 3 * og_b) // 2 is divisble by 4)
                                # if ~self.u_ogb_by_2_ogb[1]:
                                if self.inv_u_ogb3_lsb_3:
                                    # self.u = concat(self.u_ogb_by_2_ogb[self.bit_length_msb], self.u_ogb_by_2_ogb[self.bit_length_msb], self.u_ogb_by_2_ogb[self.bit_length_msb, 2])
                                    self.u_carry = self.u_ogb3_by8_carry
                                    self.u_sum = self.u_ogb3_by8_sum
                                # (u + og_b) / 2 + og_b will be even
                                # add og_b to (u + og_b) / 2, divide by 2, add og_b, divide by 2
                                # finally: (((u + og_b) / 2 + og_b) / 2 + og_b) / 2
                                else:
                                    # self.u = concat(self.u_ogb_by_2_ogb_by_2_ogb[self.bit_length_msb], self.u_ogb_by_2_ogb_by_2_ogb[self.bit_length_msb, 1])
                                    self.u_carry = self.u_ogb7_by8_carry
                                    self.u_sum = self.u_ogb7_by8_sum

                    # a divisible by 4 but not 8: reduce 2 factors of 2
                    # divide u by 4 and adjust if odd as needed
                    elif ~self.u_after_lsb_2 & ~self.u_after_lsb:
                        self.u_carry = self.u_carry_by_4
                        self.u_sum = self.u_sum_by_4

                    elif ~self.u_after_lsb:
                        self.u_carry = self.u_ogb2_by4_carry
                        self.u_sum = self.u_ogb2_by4_sum

                    elif self.inv_u_ogb_after_lsb_2:
                        self.u_carry = self.u_ogb_by4_carry
                        self.u_sum = self.u_ogb_by4_sum

                    else:
                        self.u_carry = self.u_ogb3_by4_carry
                        self.u_sum = self.u_ogb3_by4_sum

                # a is divisible by 2, not 4 so reduce 1 factor of 2
                # and add og_b to make even if needed
                elif self.u_after_lsb:
                    self.u_carry = self.u_ogb_by_2_carry
                    self.u_sum = self.u_ogb_by_2_sum
                    
                else:
                    self.u_carry = self.u_carry_by_2
                    self.u_sum = self.u_sum_by_2

            # u is not updated when b is even or not delta_sign
            elif self.b_lsb & self.delta_sign:
                # a = (a + b) // 2
                if self.shift_b_2_odd:
                    if self.u_l:
                        self.u_carry = self.u_delta_update_sub_first_carry
                        self.u_sum = self.u_delta_update_sub_first_sum

                    else:
                        self.u_carry = self.u_delta_update_sub_first_carry_out
                        self.u_sum = self.u_delta_update_sub_first_sum_out

                # a = (a + b) // 4
                elif self.a_plus_b_4:
                    if self.shift_b_8_odd & self.a_plus_b_8:
                        if self.u_delta_update_add_even:
                            if self.u_l:
                                self.u_carry = self.u_delta_update_add_carry_by_2
                                self.u_sum = self.u_delta_update_add_sum_by_2

                            else:
                                self.u_carry = self.u_delta_update_add_carry_by_2_out
                                self.u_sum = self.u_delta_update_add_sum_by_2_out
                        else:
                            if self.u_l:
                                self.u_carry = self.u_delta_update_add_ogb_by_2_carry
                                self.u_sum = self.u_delta_update_add_ogb_by_2_sum

                            else:
                                self.u_carry = self.u_delta_update_add_ogb_by_2_carry_out
                                self.u_sum = self.u_delta_update_add_ogb_by_2_sum_out
                    else:
                        if self.u_l:
                            self.u_carry = self.u_delta_update_add_carry
                            self.u_sum = self.u_delta_update_add_sum

                        else:
                            self.u_carry = self.u_delta_update_add_carry_out
                            self.u_sum = self.u_delta_update_add_sum_out
                        
                # a = (a - b) // 4
                else:
                    if self.shift_b_8_odd & self.a_minus_b_8:
                        if self.u_delta_update_sub_first_even:
                            if self.u_l:
                                self.u_carry = self.u_delta_update_sub_first_carry_by_2
                                self.u_sum = self.u_delta_update_sub_first_sum_by_2

                            else:
                                self.u_carry = self.u_delta_update_sub_first_carry_by_2_out
                                self.u_sum = self.u_delta_update_sub_first_sum_by_2_out
                        else:
                            if self.u_l:
                                self.u_carry = self.u_delta_update_sub_first_ogb_by_2_carry
                                self.u_sum = self.u_delta_update_sub_first_ogb_by_2_sum

                            else:
                                self.u_carry = self.u_delta_update_sub_first_ogb_by_2_carry_out
                                self.u_sum = self.u_delta_update_sub_first_ogb_by_2_sum_out
                    
                    else:
                        if self.u_l:
                            self.u_carry = self.u_delta_update_sub_first_carry
                            self.u_sum = self.u_delta_update_sub_first_sum

                        else:
                            self.u_carry = self.u_delta_update_sub_first_carry_out
                            self.u_sum = self.u_delta_update_sub_first_sum_out

    @always_ff((posedge, "clk"))
    def set_u_after_lsbs(self):
        if self.start:
            if self.initial_0:
                self.u_after_lsb = 0
            else:
                self.u_after_lsb = 1
            # 0 is divisble by 4 but 1 is not, but we 
            # always check div by 2 with div by 4 so 
            # this is fine for all cases for 
            # initialization (same logic for div by 8)
            self.u_after_lsb_2 = 0
            self.u_after_lsb_3 = 0
        elif ~self.done:
            if ~self.a_lsb:
                if self.shift_a_4 & ~self.a_lsb_2:
                    if self.shift_a_8 & ~self.a_lsb_3:
                        if ~self.u_after_lsb_3 & ~self.u_after_lsb_2 & ~self.u_after_lsb:
                            self.u_after_lsb = self.u_carry_by_8[0] ^ self.u_sum_by_8[0]
                            self.u_after_lsb_2 = self.u_carry_by_8[1] ^ self.u_sum_by_8[1] ^ self.u_carry_by_8[0]
                            self.u_after_lsb_3 = (self.u_carry_by_8[1] | self.u_sum_by_8[1]) ^ self.u_carry_by_8[2] ^ self.u_sum_by_8[2]
                        elif ~self.u_after_lsb_2 & ~self.u_after_lsb:
                            self.u_after_lsb = self.u_ogb4_by_8_carry[0] ^ self.u_ogb4_by_8_sum[0]
                            self.u_after_lsb_2 = self.u_ogb4_by_8_carry[1] ^ self.u_ogb4_by_8_sum[1] ^ self.u_ogb4_by_8_carry[0]
                            self.u_after_lsb_3 = (self.u_ogb4_by_8_carry[1] | self.u_ogb4_by_8_sum[1]) ^ self.u_ogb4_by_8_carry[2] ^ self.u_ogb4_by_8_sum[2]
                        elif ~self.u_after_lsb:
                            if self.inv_u_ogb2_lsb_3:
                                self.u_after_lsb = self.u_ogb2_by8_carry[0] ^ self.u_ogb2_by8_sum[0]
                                self.u_after_lsb_2 = self.u_ogb2_by8_carry[1] ^ self.u_ogb2_by8_sum[1] ^ self.u_ogb2_by8_carry[0]
                                self.u_after_lsb_3 = (self.u_ogb2_by8_carry[1] | self.u_ogb2_by8_sum[1]) ^ self.u_ogb2_by8_carry[2] ^ self.u_ogb2_by8_sum[2]
                            else:
                                self.u_after_lsb = self.u_ogb6_by8_carry[0] ^ self.u_ogb6_by8_sum[0]
                                self.u_after_lsb_2 = self.u_ogb6_by8_carry[1] ^ self.u_ogb6_by8_sum[1] ^ self.u_ogb6_by8_carry[0]
                                self.u_after_lsb_3 = (self.u_ogb6_by8_carry[1] | self.u_ogb6_by8_sum[1]) ^ self.u_ogb6_by8_carry[2] ^ self.u_ogb6_by8_sum[2]
                        else:
                            if self.inv_u_ogb_after_lsb_3 & self.inv_u_ogb_after_lsb_2:
                                self.u_after_lsb = self.u_ogb_by8_carry[0] ^ self.u_ogb_by8_sum[0]
                                self.u_after_lsb_2 = self.u_ogb_by8_carry[1] ^ self.u_ogb_by8_sum[1] ^ self.u_ogb_by8_carry[0]
                                self.u_after_lsb_3 = (self.u_ogb_by8_carry[1] | self.u_ogb_by8_sum[1]) ^ self.u_ogb_by8_carry[2] ^ self.u_ogb_by8_sum[2]
                            elif self.inv_u_ogb_after_lsb_2:
                                self.u_after_lsb = self.u_ogb5_by8_carry[0] ^ self.u_ogb5_by8_sum[0]
                                self.u_after_lsb_2 = self.u_ogb5_by8_carry[1] ^ self.u_ogb5_by8_sum[1] ^ self.u_ogb5_by8_carry[0]
                                self.u_after_lsb_3 = (self.u_ogb5_by8_carry[1] | self.u_ogb5_by8_sum[1]) ^ self.u_ogb5_by8_carry[2] ^ self.u_ogb5_by8_sum[2]
                            else:
                                if self.inv_u_ogb3_lsb_3:
                                    self.u_after_lsb = self.u_ogb3_by8_carry[0] ^ self.u_ogb3_by8_sum[0]
                                    self.u_after_lsb_2 = self.u_ogb3_by8_carry[1] ^ self.u_ogb3_by8_sum[1] ^ self.u_ogb3_by8_carry[0]
                                    self.u_after_lsb_3 = (self.u_ogb3_by8_carry[1] | self.u_ogb3_by8_sum[1]) ^ self.u_ogb3_by8_carry[2] ^ self.u_ogb3_by8_sum[2]
                                else:
                                    self.u_after_lsb = self.u_ogb7_by8_carry[0] ^ self.u_ogb7_by8_sum[0]
                                    self.u_after_lsb_2 = self.u_ogb7_by8_carry[1] ^ self.u_ogb7_by8_sum[1] ^ self.u_ogb7_by8_carry[0]
                                    self.u_after_lsb_3 = (self.u_ogb7_by8_carry[1] | self.u_ogb7_by8_sum[1]) ^ self.u_ogb7_by8_carry[2] ^ self.u_ogb7_by8_sum[2]
                    elif ~self.u_after_lsb_2 & ~self.u_after_lsb:
                        self.u_after_lsb = self.u_carry_by_4[0] ^ self.u_sum_by_4[0]
                        self.u_after_lsb_2 = self.u_carry_by_4[1] ^ self.u_sum_by_4[1] ^ self.u_carry_by_4[0]
                        self.u_after_lsb_3 = (self.u_carry_by_4[1] | self.u_sum_by_4[1]) ^ self.u_carry_by_4[2] ^ self.u_sum_by_4[2]
                    elif ~self.u_after_lsb:
                        self.u_after_lsb = self.u_ogb2_by4_carry[0] ^ self.u_ogb2_by4_sum[0]
                        self.u_after_lsb_2 = self.u_ogb2_by4_carry[1] ^ self.u_ogb2_by4_sum[1] ^ self.u_ogb2_by4_carry[0]
                        self.u_after_lsb_3 = (self.u_ogb2_by4_carry[1] | self.u_ogb2_by4_sum[1]) ^ self.u_ogb2_by4_carry[2] ^ self.u_ogb2_by4_sum[2]
                    elif self.inv_u_ogb_after_lsb_2:
                        self.u_after_lsb = self.u_ogb_by4_carry[0] ^ self.u_ogb_by4_sum[0]
                        self.u_after_lsb_2 = self.u_ogb_by4_carry[1] ^ self.u_ogb_by4_sum[1] ^ self.u_ogb_by4_carry[0]
                        self.u_after_lsb_3 = (self.u_ogb_by4_carry[1] | self.u_ogb_by4_sum[1]) ^ self.u_ogb_by4_carry[2] ^ self.u_ogb_by4_sum[2]
                    else:
                        self.u_after_lsb = self.u_ogb3_by4_carry[0] ^ self.u_ogb3_by4_sum[0]
                        self.u_after_lsb_2 = self.u_ogb3_by4_carry[1] ^ self.u_ogb3_by4_sum[1] ^ self.u_ogb3_by4_carry[0]
                        self.u_after_lsb_3 = (self.u_ogb3_by4_carry[1] | self.u_ogb3_by4_sum[1]) ^ self.u_ogb3_by4_carry[2] ^ self.u_ogb3_by4_sum[2]
                elif self.u_after_lsb:
                    self.u_after_lsb = self.u_ogb_by_2_carry[0] ^ self.u_ogb_by_2_sum[0]
                    self.u_after_lsb_2 = self.u_ogb_by_2_carry[1] ^ self.u_ogb_by_2_sum[1] ^ self.u_ogb_by_2_carry[0]
                    self.u_after_lsb_3 = (self.u_ogb_by_2_carry[1] | self.u_ogb_by_2_sum[1]) ^ self.u_ogb_by_2_carry[2] ^ self.u_ogb_by_2_sum[2]
                else:
                    self.u_after_lsb = self.u_carry_by_2[0] ^ self.u_sum_by_2[0]
                    self.u_after_lsb_2 = self.u_carry_by_2[1] ^ self.u_sum_by_2[1] ^ self.u_carry_by_2[0]
                    self.u_after_lsb_3 = (self.u_carry_by_2[1] | self.u_sum_by_2[1]) ^ self.u_carry_by_2[2] ^ self.u_sum_by_2[2]
            elif self.b_lsb & self.delta_sign:
                if self.shift_b_2_odd:
                    if self.u_l:
                        self.u_after_lsb = self.u_delta_update_sub_first_carry[0] ^ self.u_delta_update_sub_first_sum[0]
                        self.u_after_lsb_2 = self.u_delta_update_sub_first_carry[1] ^ self.u_delta_update_sub_first_sum[1] ^ self.u_delta_update_sub_first_carry[0]
                        self.u_after_lsb_3 = (self.u_delta_update_sub_first_carry[1] | self.u_delta_update_sub_first_sum[1]) ^ self.u_delta_update_sub_first_carry[2] ^ self.u_delta_update_sub_first_sum[2]
                    else:
                        self.u_after_lsb = self.u_delta_update_sub_first_carry_out[0] ^ self.u_delta_update_sub_first_sum_out[0]
                        self.u_after_lsb_2 = self.u_delta_update_sub_first_carry_out[1] ^ self.u_delta_update_sub_first_sum_out[1] ^ self.u_delta_update_sub_first_carry_out[0]
                        self.u_after_lsb_3 = (self.u_delta_update_sub_first_carry_out[1] | self.u_delta_update_sub_first_sum_out[1]) ^ self.u_delta_update_sub_first_carry_out[2] ^ self.u_delta_update_sub_first_sum_out[2]
                elif self.a_plus_b_4:
                    if self.shift_b_8_odd & self.a_plus_b_8:
                        if self.u_delta_update_add_even:
                            if self.u_l:
                                self.u_after_lsb = self.u_delta_update_add_carry_by_2[0] ^ self.u_delta_update_add_sum_by_2[0]
                                self.u_after_lsb_2 = self.u_delta_update_add_carry_by_2[1] ^ self.u_delta_update_add_sum_by_2[1] ^ self.u_delta_update_add_carry_by_2[0]
                                self.u_after_lsb_3 = (self.u_delta_update_add_carry_by_2[1] | self.u_delta_update_add_sum_by_2[1]) ^ self.u_delta_update_add_carry_by_2[2] ^ self.u_delta_update_add_sum_by_2[2]
                            else:
                                self.u_after_lsb = self.u_delta_update_add_carry_by_2_out[0] ^ self.u_delta_update_add_sum_by_2_out[0]
                                self.u_after_lsb_2 = self.u_delta_update_add_carry_by_2_out[1] ^ self.u_delta_update_add_sum_by_2_out[1] ^ self.u_delta_update_add_carry_by_2_out[0]
                                self.u_after_lsb_3 = (self.u_delta_update_add_carry_by_2_out[1] | self.u_delta_update_add_sum_by_2_out[1]) ^ self.u_delta_update_add_carry_by_2_out[2] ^ self.u_delta_update_add_sum_by_2_out[2]
                        else:
                            if self.u_l:
                                self.u_after_lsb = self.u_delta_update_add_ogb_by_2_carry[0] ^ self.u_delta_update_add_ogb_by_2_sum[0]
                                self.u_after_lsb_2 = self.u_delta_update_add_ogb_by_2_carry[1] ^ self.u_delta_update_add_ogb_by_2_sum[1] ^ self.u_delta_update_add_ogb_by_2_carry[0]
                                self.u_after_lsb_3 = (self.u_delta_update_add_ogb_by_2_carry[1] | self.u_delta_update_add_ogb_by_2_sum[1]) ^ self.u_delta_update_add_ogb_by_2_carry[2] ^ self.u_delta_update_add_ogb_by_2_sum[2]
                            else:
                                self.u_after_lsb = self.u_delta_update_add_ogb_by_2_carry_out[0] ^ self.u_delta_update_add_ogb_by_2_sum_out[0]
                                self.u_after_lsb_2 = self.u_delta_update_add_ogb_by_2_carry_out[1] ^ self.u_delta_update_add_ogb_by_2_sum_out[1] ^ self.u_delta_update_add_ogb_by_2_carry_out[0]
                                self.u_after_lsb_3 = (self.u_delta_update_add_ogb_by_2_carry_out[1] | self.u_delta_update_add_ogb_by_2_sum_out[1]) ^ self.u_delta_update_add_ogb_by_2_carry_out[2] ^ self.u_delta_update_add_ogb_by_2_sum_out[2]
                    else:
                        if self.u_l:
                            self.u_after_lsb = self.u_delta_update_add_carry[0] ^ self.u_delta_update_add_sum[0]
                            self.u_after_lsb_2 = self.u_delta_update_add_carry[1] ^ self.u_delta_update_add_sum[1] ^ self.u_delta_update_add_carry[0]
                            self.u_after_lsb_3 = (self.u_delta_update_add_carry[1] | self.u_delta_update_add_sum[1]) ^ self.u_delta_update_add_carry[2] ^ self.u_delta_update_add_sum[2]
                        else:
                            self.u_after_lsb = self.u_delta_update_add_carry_out[0] ^ self.u_delta_update_add_sum_out[0]
                            self.u_after_lsb_2 = self.u_delta_update_add_carry_out[1] ^ self.u_delta_update_add_sum_out[1] ^ self.u_delta_update_add_carry_out[0]
                            self.u_after_lsb_3 = (self.u_delta_update_add_carry_out[1] | self.u_delta_update_add_sum_out[1]) ^ self.u_delta_update_add_carry_out[2] ^ self.u_delta_update_add_sum_out[2]
                else:
                    if self.shift_b_8_odd & self.a_minus_b_8:
                        if self.u_delta_update_sub_first_even:
                            if self.u_l:
                                self.u_after_lsb = self.u_delta_update_sub_first_carry_by_2[0] ^ self.u_delta_update_sub_first_sum_by_2[0]
                                self.u_after_lsb_2 = self.u_delta_update_sub_first_carry_by_2[1] ^ self.u_delta_update_sub_first_sum_by_2[1] ^ self.u_delta_update_sub_first_carry_by_2[0]
                                self.u_after_lsb_3 = (self.u_delta_update_sub_first_carry_by_2[1] | self.u_delta_update_sub_first_sum_by_2[1]) ^ self.u_delta_update_sub_first_carry_by_2[2] ^ self.u_delta_update_sub_first_sum_by_2[2]
                            else:
                                self.u_after_lsb = self.u_delta_update_sub_first_carry_by_2_out[0] ^ self.u_delta_update_sub_first_sum_by_2_out[0]
                                self.u_after_lsb_2 = self.u_delta_update_sub_first_carry_by_2_out[1] ^ self.u_delta_update_sub_first_sum_by_2_out[1] ^ self.u_delta_update_sub_first_carry_by_2_out[0]
                                self.u_after_lsb_3 = (self.u_delta_update_sub_first_carry_by_2_out[1] | self.u_delta_update_sub_first_sum_by_2_out[1]) ^ self.u_delta_update_sub_first_carry_by_2_out[2] ^ self.u_delta_update_sub_first_sum_by_2_out[2]
                        else:
                            if self.u_l:
                                self.u_after_lsb = self.u_delta_update_sub_first_ogb_by_2_carry[0] ^ self.u_delta_update_sub_first_ogb_by_2_sum[0]
                                self.u_after_lsb_2 = self.u_delta_update_sub_first_ogb_by_2_carry[1] ^ self.u_delta_update_sub_first_ogb_by_2_sum[1] ^ self.u_delta_update_sub_first_ogb_by_2_carry[0]
                                self.u_after_lsb_3 = (self.u_delta_update_sub_first_ogb_by_2_carry[1] | self.u_delta_update_sub_first_ogb_by_2_sum[1]) ^ self.u_delta_update_sub_first_ogb_by_2_carry[2] ^ self.u_delta_update_sub_first_ogb_by_2_sum[2]
                            else:
                                self.u_after_lsb = self.u_delta_update_sub_first_ogb_by_2_carry_out[0] ^ self.u_delta_update_sub_first_ogb_by_2_sum_out[0]
                                self.u_after_lsb_2 = self.u_delta_update_sub_first_ogb_by_2_carry_out[1] ^ self.u_delta_update_sub_first_ogb_by_2_sum_out[1] ^ self.u_delta_update_sub_first_ogb_by_2_carry_out[0]
                                self.u_after_lsb_3 = (self.u_delta_update_sub_first_ogb_by_2_carry_out[1] | self.u_delta_update_sub_first_ogb_by_2_sum_out[1]) ^ self.u_delta_update_sub_first_ogb_by_2_carry_out[2] ^ self.u_delta_update_sub_first_ogb_by_2_sum_out[2]
                    else:
                        if self.u_l:
                            self.u_after_lsb = self.u_delta_update_sub_first_carry[0] ^ self.u_delta_update_sub_first_sum[0]
                            self.u_after_lsb_2 = self.u_delta_update_sub_first_carry[1] ^ self.u_delta_update_sub_first_sum[1] ^ self.u_delta_update_sub_first_carry[0]
                            self.u_after_lsb_3 = (self.u_delta_update_sub_first_carry[1] | self.u_delta_update_sub_first_sum[1]) ^ self.u_delta_update_sub_first_carry[2] ^ self.u_delta_update_sub_first_sum[2]
                        else:
                            self.u_after_lsb = self.u_delta_update_sub_first_carry_out[0] ^ self.u_delta_update_sub_first_sum_out[0]
                            self.u_after_lsb_2 = self.u_delta_update_sub_first_carry_out[1] ^ self.u_delta_update_sub_first_sum_out[1] ^ self.u_delta_update_sub_first_carry_out[0]
                            self.u_after_lsb_3 = (self.u_delta_update_sub_first_carry_out[1] | self.u_delta_update_sub_first_sum_out[1]) ^ self.u_delta_update_sub_first_carry_out[2] ^ self.u_delta_update_sub_first_sum_out[2]

    @always_ff((posedge, "clk"))
    def set_inv_u_ogb_after_lsb_2_add(self):
        if ~self.done:
            if ~self.a_lsb:
                if self.shift_a_4 & ~self.a_lsb_2:
                    if self.shift_a_8 & ~self.a_lsb_3:
                        if ~self.u_after_lsb_3 & ~self.u_after_lsb_2 & ~self.u_after_lsb:
                            self.inv_u_ogb_after_lsb_2 = self.u_ogb_8_carry_1[1] ^ self.u_ogb_8_sum_1[1]
                        elif ~self.u_after_lsb_2 & ~self.u_after_lsb:
                            self.inv_u_ogb_after_lsb_2 = self.u_ogb_8_carry_2[1] ^ self.u_ogb_8_sum_2[1]
                        elif ~self.u_after_lsb:
                            if self.inv_u_ogb2_lsb_3:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_8_carry_3[1] ^ self.u_ogb_8_sum_3[1]
                            else:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_8_carry_4[1] ^ self.u_ogb_8_sum_4[1]
                        else:
                            if self.inv_u_ogb_after_lsb_3 & self.inv_u_ogb_after_lsb_2:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_8_carry_5[1] ^ self.u_ogb_8_sum_5[1]
                            elif self.inv_u_ogb_after_lsb_2:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_8_carry_6[1] ^ self.u_ogb_8_sum_6[1]
                            else:
                                if self.inv_u_ogb3_lsb_3:
                                    self.inv_u_ogb_after_lsb_2 = self.u_ogb_8_carry_7[1] ^ self.u_ogb_8_sum_7[1]
                                else:
                                    self.inv_u_ogb_after_lsb_2 = self.u_ogb_8_carry_8[1] ^ self.u_ogb_8_sum_8[1]
                    elif ~self.u_after_lsb_2 & ~self.u_after_lsb:
                        self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_1[1] ^ self.u_ogb_sum_1[1]
                    elif ~self.u_after_lsb:
                        self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_2[1] ^ self.u_ogb_sum_2[1]
                    elif self.inv_u_ogb_after_lsb_2:
                        self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_3[1] ^ self.u_ogb_sum_3[1]
                    else:
                        self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_4[1] ^ self.u_ogb_sum_4[1]
                elif self.u_after_lsb:
                    self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_5[1] ^ self.u_ogb_sum_5[1]
                else:
                    self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_6[1] ^ self.u_ogb_sum_6[1]
            elif self.b_lsb & self.delta_sign:
                if self.shift_b_2_odd:
                    if self.u_l:
                        self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_8[1] ^ self.u_ogb_sum_8[1]
                    else:
                        self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_8_out[1] ^ self.u_ogb_sum_8_out[1]
                elif self.a_plus_b_4:
                    if self.shift_b_8_odd & self.a_plus_b_8:
                        if self.u_delta_update_add_even:
                            if self.u_l:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_7_by_2[1] ^ self.u_ogb_sum_7_by_2[1]
                            else:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_7_by_2_out[1] ^ self.u_ogb_sum_7_by_2_out[1]
                        else:
                            if self.u_l:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_7_ogb_by_2[1] ^ self.u_ogb_sum_7_ogb_by_2[1]
                            else:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_7_ogb_by_2_out[1] ^ self.u_ogb_sum_7_ogb_by_2_out[1]
                    else:
                        if self.u_l:
                            self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_7[1] ^ self.u_ogb_sum_7[1]
                        else:
                            self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_7_out[1] ^ self.u_ogb_sum_7_out[1]
                else:
                    if self.shift_b_8_odd & self.a_minus_b_8:
                        if self.u_delta_update_sub_first_even:
                            if self.u_l:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_8_by_2[1] ^ self.u_ogb_sum_8_by_2[1]
                            else:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_8_by_2_out[1] ^ self.u_ogb_sum_8_by_2_out[1]
                        else:
                            if self.u_l:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_8_ogb_by_2[1] ^ self.u_ogb_sum_8_ogb_by_2[1]
                            else:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_8_ogb_by_2_out[1] ^ self.u_ogb_sum_8_ogb_by_2_out[1]
                    else:
                        if self.u_l:
                            self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_8[1] ^ self.u_ogb_sum_8[1]
                        else:
                            self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_8_out[1] ^ self.u_ogb_sum_8_out[1]

    @always_ff((posedge, "clk"))
    def set_inv_u_ogb_after_lsb_2_sub(self):
        if ~self.done:
            if ~self.a_lsb:
                if self.shift_a_4 & ~self.a_lsb_2:
                    if self.shift_a_8 & ~self.a_lsb_3:
                        if ~self.u_after_lsb_3 & ~self.u_after_lsb_2 & ~self.u_after_lsb:
                            self.inv_u_ogb_after_lsb_2 = self.u_ogb_8_carry_1[1] & self.u_ogb_8_sum_1[1]
                        elif ~self.u_after_lsb_2 & ~self.u_after_lsb:
                            self.inv_u_ogb_after_lsb_2 = self.u_ogb_8_carry_2[1] & self.u_ogb_8_sum_2[1]
                        elif ~self.u_after_lsb:
                            if self.inv_u_ogb2_lsb_3:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_8_carry_3[1] & self.u_ogb_8_sum_3[1]
                            else:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_8_carry_4[1] & self.u_ogb_8_sum_4[1]
                        else:
                            if self.inv_u_ogb_after_lsb_3 & self.inv_u_ogb_after_lsb_2:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_8_carry_5[1] & self.u_ogb_8_sum_5[1]
                            elif self.inv_u_ogb_after_lsb_2:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_8_carry_6[1] & self.u_ogb_8_sum_6[1]
                            else:
                                if self.inv_u_ogb3_lsb_3:
                                    self.inv_u_ogb_after_lsb_2 = self.u_ogb_8_carry_7[1] & self.u_ogb_8_sum_7[1]
                                else:
                                    self.inv_u_ogb_after_lsb_2 = self.u_ogb_8_carry_8[1] & self.u_ogb_8_sum_8[1]
                    elif ~self.u_after_lsb_2 & ~self.u_after_lsb:
                        self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_1[1] & self.u_ogb_sum_1[1]
                    elif ~self.u_after_lsb:
                        self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_2[1] & self.u_ogb_sum_2[1]
                    elif self.inv_u_ogb_after_lsb_2:
                        self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_3[1] & self.u_ogb_sum_3[1]
                    else:
                        self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_4[1] & self.u_ogb_sum_4[1]
                elif self.u_after_lsb:
                    self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_5[1] & self.u_ogb_sum_5[1]
                else:
                    self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_6[1] & self.u_ogb_sum_6[1]
            elif self.b_lsb & self.delta_sign:
                if self.shift_b_2_odd:
                    if self.u_l:
                        self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_8[1] & self.u_ogb_sum_8[1]
                    else:
                        self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_8_out[1] & self.u_ogb_sum_8_out[1]
                elif self.a_plus_b_4:
                    if self.shift_b_8_odd & self.a_plus_b_8:
                        if self.u_delta_update_add_even:
                            if self.u_l:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_7_by_2[1] & self.u_ogb_sum_7_by_2[1]
                            else:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_7_by_2_out[1] & self.u_ogb_sum_7_by_2_out[1]
                        else:
                            if self.u_l:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_7_ogb_by_2[1] & self.u_ogb_sum_7_ogb_by_2[1]
                            else:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_7_ogb_by_2_out[1] & self.u_ogb_sum_7_ogb_by_2_out[1]
                    else:
                        if self.u_l:
                            self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_7[1] & self.u_ogb_sum_7[1]
                        else:
                            self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_7_out[1] & self.u_ogb_sum_7_out[1]
                else:
                    if self.shift_b_8_odd & self.a_minus_b_8:
                        if self.u_delta_update_sub_first_even:
                            if self.u_l:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_8_by_2[1] & self.u_ogb_sum_8_by_2[1]
                            else:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_8_by_2_out[1] & self.u_ogb_sum_8_by_2_out[1]
                        else:
                            if self.u_l:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_8_ogb_by_2[1] & self.u_ogb_sum_8_ogb_by_2[1]
                            else:
                                self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_8_ogb_by_2_out[1] & self.u_ogb_sum_8_ogb_by_2_out[1]
                    else:
                        if self.u_l:
                            self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_8[1] & self.u_ogb_sum_8[1]
                        else:
                            self.inv_u_ogb_after_lsb_2 = self.u_ogb_carry_8_out[1] & self.u_ogb_sum_8_out[1]

    @always_ff((posedge, "clk"))
    def set_inv_u_ogb_after_lsb_3(self):
        if ~self.done:
            if ~self.a_lsb:
                if self.shift_a_4 & ~self.a_lsb_2:
                    if self.shift_a_8 & ~self.a_lsb_3:
                        if ~self.u_after_lsb_3 & ~self.u_after_lsb_2 & ~self.u_after_lsb:
                            self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_8_carry_1[1] | self.u_ogb_8_sum_1[1]) ^ self.u_ogb_8_carry_1[2] ^ self.u_ogb_8_sum_1[2])
                        elif ~self.u_after_lsb_2 & ~self.u_after_lsb:
                            self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_8_carry_2[1] | self.u_ogb_8_sum_2[1]) ^ self.u_ogb_8_carry_2[2] ^ self.u_ogb_8_sum_2[2])
                        elif ~self.u_after_lsb:
                            if self.inv_u_ogb2_lsb_3:
                                self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_8_carry_3[1] | self.u_ogb_8_sum_3[1]) ^ self.u_ogb_8_carry_3[2] ^ self.u_ogb_8_sum_3[2])
                            else:
                                self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_8_carry_4[1] | self.u_ogb_8_sum_4[1]) ^ self.u_ogb_8_carry_4[2] ^ self.u_ogb_8_sum_4[2])
                        else:
                            if self.inv_u_ogb_after_lsb_3 & self.inv_u_ogb_after_lsb_2:
                                self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_8_carry_5[1] | self.u_ogb_8_sum_5[1]) ^ self.u_ogb_8_carry_5[2] ^ self.u_ogb_8_sum_5[2])

                            elif self.inv_u_ogb_after_lsb_2:
                                self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_8_carry_6[1] | self.u_ogb_8_sum_6[1]) ^ self.u_ogb_8_carry_6[2] ^ self.u_ogb_8_sum_6[2])
                            else:
                                if self.inv_u_ogb3_lsb_3:
                                    self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_8_carry_7[1] | self.u_ogb_8_sum_7[1]) ^ self.u_ogb_8_carry_7[2] ^ self.u_ogb_8_sum_7[2])
                                else:
                                    self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_8_carry_8[1] | self.u_ogb_8_sum_8[1]) ^ self.u_ogb_8_carry_8[2] ^ self.u_ogb_8_sum_8[2])
                    elif ~self.u_after_lsb_2 & ~self.u_after_lsb:
                        self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_carry_1[1] | self.u_ogb_sum_1[1]) ^ self.u_ogb_carry_1[2] ^ self.u_ogb_sum_1[2])
                    elif ~self.u_after_lsb:
                        self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_carry_2[1] | self.u_ogb_sum_2[1]) ^ self.u_ogb_carry_2[2] ^ self.u_ogb_sum_2[2])
                    elif self.inv_u_ogb_after_lsb_2:
                        self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_carry_3[1] | self.u_ogb_sum_3[1]) ^ self.u_ogb_carry_3[2] ^ self.u_ogb_sum_3[2])
                    else:
                        self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_carry_4[1] | self.u_ogb_sum_4[1]) ^ self.u_ogb_carry_4[2] ^ self.u_ogb_sum_4[2])
                elif self.u_after_lsb:
                    self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_carry_5[1] | self.u_ogb_sum_5[1]) ^ self.u_ogb_carry_5[2] ^ self.u_ogb_sum_5[2])
                else:
                    self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_carry_6[1] | self.u_ogb_sum_6[1]) ^ self.u_ogb_carry_6[2] ^ self.u_ogb_sum_6[2])
            elif self.b_lsb & self.delta_sign:
                if self.shift_b_2_odd:
                    if self.u_l:
                        self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_carry_8[1] | self.u_ogb_sum_8[1]) ^ self.u_ogb_carry_8[2] ^ self.u_ogb_sum_8[2])
                    else:
                        self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_carry_8_out[1] | self.u_ogb_sum_8_out[1]) ^ self.u_ogb_carry_8_out[2] ^ self.u_ogb_sum_8_out[2])
                elif self.a_plus_b_4:
                    if self.shift_b_8_odd & self.a_plus_b_8:
                        if self.u_delta_update_add_even:
                            if self.u_l:
                                self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_carry_7_by_2[1] | self.u_ogb_sum_7_by_2[1]) ^ self.u_ogb_carry_7_by_2[2] ^ self.u_ogb_sum_7_by_2[2])
                            else:
                                self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_carry_7_by_2_out[1] | self.u_ogb_sum_7_by_2_out[1]) ^ self.u_ogb_carry_7_by_2_out[2] ^ self.u_ogb_sum_7_by_2_out[2])
                        else:
                            if self.u_l:
                                self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_carry_7_ogb_by_2[1] | self.u_ogb_sum_7_ogb_by_2[1]) ^ self.u_ogb_carry_7_ogb_by_2[2] ^ self.u_ogb_sum_7_ogb_by_2[2])
                            else:
                                self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_carry_7_ogb_by_2_out[1] | self.u_ogb_sum_7_ogb_by_2_out[1]) ^ self.u_ogb_carry_7_ogb_by_2_out[2] ^ self.u_ogb_sum_7_ogb_by_2_out[2])
                    else:
                        if self.u_l:
                            self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_carry_7[1] | self.u_ogb_sum_7[1]) ^ self.u_ogb_carry_7[2] ^ self.u_ogb_sum_7[2])
                        else:
                            self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_carry_7_out[1] | self.u_ogb_sum_7_out[1]) ^ self.u_ogb_carry_7_out[2] ^ self.u_ogb_sum_7_out[2])
                else:
                    if self.shift_b_8_odd & self.a_minus_b_8:
                        if self.u_delta_update_sub_first_even:
                            if self.u_l:
                                self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_carry_8_by_2[1] | self.u_ogb_sum_8_by_2[1]) ^ self.u_ogb_carry_8_by_2[2] ^ self.u_ogb_sum_8_by_2[2])
                            else:
                                self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_carry_8_by_2_out[1] | self.u_ogb_sum_8_by_2_out[1]) ^ self.u_ogb_carry_8_by_2_out[2] ^ self.u_ogb_sum_8_by_2_out[2])
                        else:
                            if self.u_l:
                                self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_carry_8_ogb_by_2[1] | self.u_ogb_sum_8_ogb_by_2[1]) ^ self.u_ogb_carry_8_ogb_by_2[2] ^ self.u_ogb_sum_8_ogb_by_2[2])
                            else:
                                self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_carry_8_ogb_by_2_out[1] | self.u_ogb_sum_8_ogb_by_2_out[1]) ^ self.u_ogb_carry_8_ogb_by_2_out[2] ^ self.u_ogb_sum_8_ogb_by_2_out[2])
                    else:
                        if self.u_l:
                            self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_carry_8[1] | self.u_ogb_sum_8[1]) ^ self.u_ogb_carry_8[2] ^ self.u_ogb_sum_8[2])
                        else:
                            self.inv_u_ogb_after_lsb_3 = ~((self.u_ogb_carry_8_out[1] | self.u_ogb_sum_8_out[1]) ^ self.u_ogb_carry_8_out[2] ^ self.u_ogb_sum_8_out[2])

    @always_comb
    def set_u_y_after_lsbs(self):
        if ~self.done:
            if ~self.a_lsb:
                if self.shift_a_4 & ~self.a_lsb_2:
                    if self.shift_a_8 & ~self.a_lsb_3:
                        if ~self.u_after_lsb_3 & ~self.u_after_lsb_2 & ~self.u_after_lsb:
                            self.u_y_after_lsb = self.uy_after_carry_8_1[0] ^ self.uy_after_sum_8_1[0]
                            self.u_y_after_lsb_sub = self.uy_after_sub_carry_8_1[0] ^ self.uy_after_sub_sum_8_1[0]
                            self.u_y_after_lsb_2 = self.uy_after_carry_8_1[1] ^ self.uy_after_sum_8_1[1] ^ self.uy_after_carry_8_1[0]
                            self.u_y_after_lsb_2_sub = self.uy_after_sub_carry_8_1[1] ^ self.uy_after_sub_sum_8_1[1] ^ self.uy_after_sub_carry_8_1[0]
                        elif ~self.u_after_lsb_2 & ~self.u_after_lsb:
                            self.u_y_after_lsb = self.uy_after_carry_8_2[0] ^ self.uy_after_sum_8_2[0]
                            self.u_y_after_lsb_sub = self.uy_after_sub_carry_8_2[0] ^ self.uy_after_sub_sum_8_2[0]
                            self.u_y_after_lsb_2 = self.uy_after_carry_8_2[1] ^ self.uy_after_sum_8_2[1] ^ self.uy_after_carry_8_2[0]
                            self.u_y_after_lsb_2_sub = self.uy_after_sub_carry_8_2[1] ^ self.uy_after_sub_sum_8_2[1] ^ self.uy_after_sub_carry_8_2[0]
                        elif ~self.u_after_lsb:
                            if self.inv_u_ogb2_lsb_3:
                                self.u_y_after_lsb = self.uy_after_carry_8_3[0] ^ self.uy_after_sum_8_3[0]
                                self.u_y_after_lsb_sub = self.uy_after_sub_carry_8_3[0] ^ self.uy_after_sub_sum_8_3[0]
                                self.u_y_after_lsb_2 = self.uy_after_carry_8_3[1] ^ self.uy_after_sum_8_3[1] ^ self.uy_after_carry_8_3[0]
                                self.u_y_after_lsb_2_sub = self.uy_after_sub_carry_8_3[1] ^ self.uy_after_sub_sum_8_3[1] ^ self.uy_after_sub_carry_8_3[0]
                            else:
                                self.u_y_after_lsb = self.uy_after_carry_8_4[0] ^ self.uy_after_sum_8_4[0]
                                self.u_y_after_lsb_sub = self.uy_after_sub_carry_8_4[0] ^ self.uy_after_sub_sum_8_4[0]
                                self.u_y_after_lsb_2 = self.uy_after_carry_8_4[1] ^ self.uy_after_sum_8_4[1] ^ self.uy_after_carry_8_4[0]
                                self.u_y_after_lsb_2_sub = self.uy_after_sub_carry_8_4[1] ^ self.uy_after_sub_sum_8_4[1] ^ self.uy_after_sub_carry_8_4[0]
                        else:
                            if self.inv_u_ogb_after_lsb_3 & self.inv_u_ogb_after_lsb_2:
                                self.u_y_after_lsb = self.uy_after_carry_8_5[0] ^ self.uy_after_sum_8_5[0]
                                self.u_y_after_lsb_sub = self.uy_after_sub_carry_8_5[0] ^ self.uy_after_sub_sum_8_5[0]
                                self.u_y_after_lsb_2 = self.uy_after_carry_8_5[1] ^ self.uy_after_sum_8_5[1] ^ self.uy_after_carry_8_5[0]
                                self.u_y_after_lsb_2_sub = self.uy_after_sub_carry_8_5[1] ^ self.uy_after_sub_sum_8_5[1] ^ self.uy_after_sub_carry_8_5[0]
                            elif self.inv_u_ogb_after_lsb_2:
                                self.u_y_after_lsb = self.uy_after_carry_8_6[0] ^ self.uy_after_sum_8_6[0]
                                self.u_y_after_lsb_sub = self.uy_after_sub_carry_8_6[0] ^ self.uy_after_sub_sum_8_6[0]
                                self.u_y_after_lsb_2 = self.uy_after_carry_8_6[1] ^ self.uy_after_sum_8_6[1] ^ self.uy_after_carry_8_6[0]
                                self.u_y_after_lsb_2_sub = self.uy_after_sub_carry_8_6[1] ^ self.uy_after_sub_sum_8_6[1] ^ self.uy_after_sub_carry_8_6[0]
                            else:
                                if self.inv_u_ogb3_lsb_3:
                                    self.u_y_after_lsb = self.uy_after_carry_8_7[0] ^ self.uy_after_sum_8_7[0]
                                    self.u_y_after_lsb_sub = self.uy_after_sub_carry_8_7[0] ^ self.uy_after_sub_sum_8_7[0]
                                    self.u_y_after_lsb_2 = self.uy_after_carry_8_7[1] ^ self.uy_after_sum_8_7[1] ^ self.uy_after_carry_8_7[0]
                                    self.u_y_after_lsb_2_sub = self.uy_after_sub_carry_8_7[1] ^ self.uy_after_sub_sum_8_7[1] ^ self.uy_after_sub_carry_8_7[0]
                                else:
                                    self.u_y_after_lsb = self.uy_after_carry_8_8[0] ^ self.uy_after_sum_8_8[0]
                                    self.u_y_after_lsb_sub = self.uy_after_sub_carry_8_8[0] ^ self.uy_after_sub_sum_8_8[0]
                                    self.u_y_after_lsb_2 = self.uy_after_carry_8_8[1] ^ self.uy_after_sum_8_8[1] ^ self.uy_after_carry_8_8[0]
                                    self.u_y_after_lsb_2_sub = self.uy_after_sub_carry_8_8[1] ^ self.uy_after_sub_sum_8_8[1] ^ self.uy_after_sub_carry_8_8[0]
                    elif ~self.u_after_lsb_2 & ~self.u_after_lsb:
                        self.u_y_after_lsb = self.uy_after_carry1[0] ^ self.uy_after_sum1[0]
                        self.u_y_after_lsb_sub = self.uy_after_carry1_sub[0] ^ self.uy_after_sum1_sub[0]
                        self.u_y_after_lsb_2 = self.uy_after_carry1[1] ^ self.uy_after_sum1[1] ^ self.uy_after_carry1[0]
                        self.u_y_after_lsb_2_sub = self.uy_after_carry1_sub[1] ^ self.uy_after_sum1_sub[1] ^ self.uy_after_carry1_sub[0]
                    elif ~self.u_after_lsb:
                        self.u_y_after_lsb = self.uy_after_carry2[0] ^ self.uy_after_sum2[0]
                        self.u_y_after_lsb_sub = self.uy_after_carry2_sub[0] ^ self.uy_after_sum2_sub[0]
                        self.u_y_after_lsb_2 = self.uy_after_carry2[1] ^ self.uy_after_sum2[1] ^ self.uy_after_carry2[0]
                        self.u_y_after_lsb_2_sub = self.uy_after_carry2_sub[1] ^ self.uy_after_sum2_sub[1] ^ self.uy_after_carry2_sub[0]
                    elif self.inv_u_ogb_after_lsb_2:
                        self.u_y_after_lsb = self.uy_after_carry3[0] ^ self.uy_after_sum3[0]
                        self.u_y_after_lsb_sub = self.uy_after_carry3_sub[0] ^ self.uy_after_sum3_sub[0]
                        self.u_y_after_lsb_2 = self.uy_after_carry3[1] ^ self.uy_after_sum3[1] ^ self.uy_after_carry3[0]
                        self.u_y_after_lsb_2_sub = self.uy_after_carry3_sub[1] ^ self.uy_after_sum3_sub[1] ^ self.uy_after_carry3_sub[0]
                    else:
                        self.u_y_after_lsb = self.uy_after_carry4[0] ^ self.uy_after_sum4[0]
                        self.u_y_after_lsb_sub = self.uy_after_carry4_sub[0] ^ self.uy_after_sum4_sub[0]
                        self.u_y_after_lsb_2 = self.uy_after_carry4[1] ^ self.uy_after_sum4[1] ^ self.uy_after_carry4[0]
                        self.u_y_after_lsb_2_sub = self.uy_after_carry4_sub[1] ^ self.uy_after_sum4_sub[1] ^ self.uy_after_carry4_sub[0]
                elif self.u_after_lsb:
                    self.u_y_after_lsb = self.uy_after_carry5[0] ^ self.uy_after_sum5[0]
                    self.u_y_after_lsb_sub = self.uy_after_carry5_sub[0] ^ self.uy_after_sum5_sub[0]
                    self.u_y_after_lsb_2 = self.uy_after_carry5[1] ^ self.uy_after_sum5[1] ^ self.uy_after_carry5[0]
                    self.u_y_after_lsb_2_sub = self.uy_after_carry5_sub[1] ^ self.uy_after_sum5_sub[1] ^ self.uy_after_carry5_sub[0]
                else:
                    self.u_y_after_lsb = self.uy_after_carry6[0] ^ self.uy_after_sum6[0]
                    self.u_y_after_lsb_sub = self.uy_after_carry6_sub[0] ^ self.uy_after_sum6_sub[0]
                    self.u_y_after_lsb_2 = self.uy_after_carry6[1] ^ self.uy_after_sum6[1] ^ self.uy_after_carry6[0]
                    self.u_y_after_lsb_2_sub = self.uy_after_carry6_sub[1] ^ self.uy_after_sum6_sub[1] ^ self.uy_after_carry6_sub[0]
            elif self.b_lsb & self.delta_sign:
                if self.shift_b_2_odd:
                    self.u_y_after_lsb = self.uy_sub_after_carry[0] ^ self.uy_sub_after_sum[0]
                    self.u_y_after_lsb_sub = self.uy_sub_after_carry_sub[0] ^ self.uy_sub_after_sum_sub[0]
                    self.u_y_after_lsb_2 = self.uy_sub_after_carry[1] ^ self.uy_sub_after_sum[1] ^ self.uy_sub_after_carry[0]
                    self.u_y_after_lsb_2_sub = self.uy_sub_after_carry_sub[1] ^ self.uy_sub_after_sum_sub[1] ^ self.uy_sub_after_carry_sub[0]
                elif self.a_plus_b_4:
                    if self.shift_b_8_odd & self.a_plus_b_8:
                        if self.u_delta_update_add_even:
                            self.u_y_after_lsb = self.uy_add_after_by_2_carry[0] ^ self.uy_add_after_by_2_sum[0]
                            self.u_y_after_lsb_sub = self.uy_add_after_by_2_carry_sub[0] ^ self.uy_add_after_by_2_sum_sub[0]
                            self.u_y_after_lsb_2 = self.uy_add_after_by_2_carry[1] ^ self.uy_add_after_by_2_sum[1] ^ self.uy_add_after_by_2_carry[0]
                            self.u_y_after_lsb_2_sub = self.uy_add_after_by_2_carry_sub[1] ^ self.uy_add_after_by_2_sum_sub[1] ^ self.uy_add_after_by_2_carry_sub[0]
                        else:
                            self.u_y_after_lsb = self.uy_add_after_ogb_by_2_carry[0] ^ self.uy_add_after_ogb_by_2_sum[0]
                            self.u_y_after_lsb_sub = self.uy_add_after_ogb_by_2_carry_sub[0] ^ self.uy_add_after_ogb_by_2_sum_sub[0]
                            self.u_y_after_lsb_2 = self.uy_add_after_ogb_by_2_carry[1] ^ self.uy_add_after_ogb_by_2_sum[1] ^ self.uy_add_after_ogb_by_2_carry[0]
                            self.u_y_after_lsb_2_sub = self.uy_add_after_ogb_by_2_carry_sub[1] ^ self.uy_add_after_ogb_by_2_sum_sub[1] ^ self.uy_add_after_ogb_by_2_carry_sub[0]
                    else:
                        self.u_y_after_lsb = self.uy_add_after_carry[0] ^ self.uy_add_after_sum[0]
                        self.u_y_after_lsb_sub = self.uy_add_after_carry_sub[0] ^ self.uy_add_after_sum_sub[0]
                        self.u_y_after_lsb_2 = self.uy_add_after_carry[1] ^ self.uy_add_after_sum[1] ^ self.uy_add_after_carry[0]
                        self.u_y_after_lsb_2_sub = self.uy_add_after_carry_sub[1] ^ self.uy_add_after_sum_sub[1] ^ self.uy_add_after_carry_sub[0]
                else:
                    if self.shift_b_8_odd & self.a_minus_b_8:
                        if self.u_delta_update_sub_first_even:
                            self.u_y_after_lsb = self.uy_sub_after_by_2_carry[0] ^ self.uy_sub_after_by_2_sum[0]
                            self.u_y_after_lsb_sub = self.uy_sub_after_by_2_carry_sub[0] ^ self.uy_sub_after_by_2_sum_sub[0]
                            self.u_y_after_lsb_2 = self.uy_sub_after_by_2_carry[1] ^ self.uy_sub_after_by_2_sum[1] ^ self.uy_sub_after_by_2_carry[0]
                            self.u_y_after_lsb_2_sub = self.uy_sub_after_by_2_carry_sub[1] ^ self.uy_sub_after_by_2_sum_sub[1] ^ self.uy_sub_after_by_2_carry_sub[0]
                        else:
                            self.u_y_after_lsb = self.uy_sub_after_ogb_by_2_carry[0] ^ self.uy_sub_after_ogb_by_2_sum[0]
                            self.u_y_after_lsb_sub = self.uy_sub_after_ogb_by_2_carry_sub[0] ^ self.uy_sub_after_ogb_by_2_sum_sub[0]
                            self.u_y_after_lsb_2 = self.uy_sub_after_ogb_by_2_carry[1] ^ self.uy_sub_after_ogb_by_2_sum[1] ^ self.uy_sub_after_ogb_by_2_carry[0]
                            self.u_y_after_lsb_2_sub = self.uy_sub_after_ogb_by_2_carry_sub[1] ^ self.uy_sub_after_ogb_by_2_sum_sub[1] ^ self.uy_sub_after_ogb_by_2_carry_sub[0]
                    else:
                        self.u_y_after_lsb = self.uy_sub_after_carry[0] ^ self.uy_sub_after_sum[0]
                        self.u_y_after_lsb_sub = self.uy_sub_after_carry_sub[0] ^ self.uy_sub_after_sum_sub[0]
                        self.u_y_after_lsb_2 = self.uy_sub_after_carry[1] ^ self.uy_sub_after_sum[1] ^ self.uy_sub_after_carry[0]
                        self.u_y_after_lsb_2_sub = self.uy_sub_after_carry_sub[1] ^ self.uy_sub_after_sum_sub[1] ^ self.uy_sub_after_carry_sub[0]
            else:
                self.u_y_after_lsb = 0
                self.u_y_after_lsb_sub = 0
                self.u_y_after_lsb_2 = 0
                self.u_y_after_lsb_2_sub = 0
        else:
            self.u_y_after_lsb = 0
            self.u_y_after_lsb_sub = 0
            self.u_y_after_lsb_2 = 0
            self.u_y_after_lsb_2_sub = 0

    @always_comb
    def set_inv_u_y_ogb_after_lsb_2_add(self):
        if ~self.done:
            if ~self.a_lsb:
                if self.shift_a_4 & ~self.a_lsb_2:
                    if self.shift_a_8 & ~self.a_lsb_3:
                        if ~self.u_after_lsb_3 & ~self.u_after_lsb_2 & ~self.u_after_lsb:
                            self.inv_u_y_ogb_after_lsb_2 = self.uyb_8_after_carry1[1] ^ self.uyb_8_after_sum1[1]
                            self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_8_after_sub_carry1[1] ^ self.uyb_8_after_sub_sum1[1]
                            self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uy_after_sub_switch_carry_8_1[1] ^ self.uy_after_sub_switch_sum_8_1[1]
                        elif ~self.u_after_lsb_2 & ~self.u_after_lsb:
                            self.inv_u_y_ogb_after_lsb_2 = self.uyb_8_after_carry2[1] ^ self.uyb_8_after_sum2[1]
                            self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_8_after_sub_carry2[1] ^ self.uyb_8_after_sub_sum2[1]
                            self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uy_after_sub_switch_carry_8_2[1] ^ self.uy_after_sub_switch_sum_8_2[1]
                        elif ~self.u_after_lsb:
                            if self.inv_u_ogb2_lsb_3:
                                self.inv_u_y_ogb_after_lsb_2 = self.uyb_8_after_carry3[1] ^ self.uyb_8_after_sum3[1]
                                self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_8_after_sub_carry3[1] ^ self.uyb_8_after_sub_sum3[1]
                                self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uy_after_sub_switch_carry_8_3[1] ^ self.uy_after_sub_switch_sum_8_3[1]
                            else:
                                self.inv_u_y_ogb_after_lsb_2 = self.uyb_8_after_carry4[1] ^ self.uyb_8_after_sum4[1]
                                self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_8_after_sub_carry4[1] ^ self.uyb_8_after_sub_sum4[1]
                                self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uy_after_sub_switch_carry_8_4[1] ^ self.uy_after_sub_switch_sum_8_4[1]
                        else:
                            if self.inv_u_ogb_after_lsb_3 & self.inv_u_ogb_after_lsb_2:
                                self.inv_u_y_ogb_after_lsb_2 = self.uyb_8_after_carry5[1] ^ self.uyb_8_after_sum5[1]
                                self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_8_after_sub_carry5[1] ^ self.uyb_8_after_sub_sum5[1]
                                self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uy_after_sub_switch_carry_8_5[1] ^ self.uy_after_sub_switch_sum_8_5[1]
                            elif self.inv_u_ogb_after_lsb_2:
                                self.inv_u_y_ogb_after_lsb_2 = self.uyb_8_after_carry6[1] ^ self.uyb_8_after_sum6[1]
                                self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_8_after_sub_carry6[1] ^ self.uyb_8_after_sub_sum6[1]
                                self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uy_after_sub_switch_carry_8_6[1] ^ self.uy_after_sub_switch_sum_8_6[1]
                            else:
                                if self.inv_u_ogb3_lsb_3:
                                    self.inv_u_y_ogb_after_lsb_2 = self.uyb_8_after_carry7[1] ^ self.uyb_8_after_sum7[1]
                                    self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_8_after_sub_carry7[1] ^ self.uyb_8_after_sub_sum7[1]
                                    self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uy_after_sub_switch_carry_8_7[1] ^ self.uy_after_sub_switch_sum_8_7[1]
                                else:
                                    self.inv_u_y_ogb_after_lsb_2 = self.uyb_8_after_carry8[1] ^ self.uyb_8_after_sum8[1]
                                    self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_8_after_sub_carry8[1] ^ self.uyb_8_after_sub_sum8[1]
                                    self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uy_after_sub_switch_carry_8_8[1] ^ self.uy_after_sub_switch_sum_8_8[1]
                    elif ~self.u_after_lsb_2 & ~self.u_after_lsb:
                        self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carry1[1] ^ self.uyb_after_sum1[1]
                        self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carry1_sub[1] ^ self.uyb_after_sum1_sub[1]
                        self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carry1_sub_switch[1] ^ self.uyb_after_sum1_sub_switch[1]
                    elif ~self.u_after_lsb:
                        self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carry2[1] ^ self.uyb_after_sum2[1]
                        self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carry2_sub[1] ^ self.uyb_after_sum2_sub[1]
                        self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carry2_sub_switch[1] ^ self.uyb_after_sum2_sub_switch[1]
                    elif self.inv_u_ogb_after_lsb_2:
                        self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carry3[1] ^ self.uyb_after_sum3[1]
                        self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carry3_sub[1] ^ self.uyb_after_sum3_sub[1]
                        self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carry3_sub_switch[1] ^ self.uyb_after_sum3_sub_switch[1]
                    else:
                        self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carry4[1] ^ self.uyb_after_sum4[1]
                        self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carry4_sub[1] ^ self.uyb_after_sum4_sub[1]
                        self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carry4_sub_switch[1] ^ self.uyb_after_sum4_sub_switch[1]
                elif self.u_after_lsb:
                    self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carry5[1] ^ self.uyb_after_sum5[1]
                    self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carry5_sub[1] ^ self.uyb_after_sum5_sub[1]
                    self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carry5_sub_switch[1] ^ self.uyb_after_sum5_sub_switch[1]
                else:
                    self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carry6[1] ^ self.uyb_after_sum6[1]
                    self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carry6_sub[1] ^ self.uyb_after_sum6_sub[1]
                    self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carry6_sub_switch[1] ^ self.uyb_after_sum6_sub_switch[1]
            elif self.b_lsb & self.delta_sign:
                if self.shift_b_2_odd:
                    self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carrysub[1] ^ self.uyb_after_sumsub[1]
                    self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carrysub_sub[1] ^ self.uyb_after_sumsub_sub[1]
                    self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carrysub_sub_switch[1] ^ self.uyb_after_sumsub_sub_switch[1]
                elif self.a_plus_b_4:
                    if self.shift_b_8_odd & self.a_plus_b_8:
                        if self.u_delta_update_add_even:
                            self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carry_by_2_add[1] ^ self.uyb_after_sum_by_2_add[1]
                            self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carry_by_2_add_sub[1] ^ self.uyb_after_sum_by_2_add_sub[1]
                            self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carryadd_sub_by_2_switch[1] ^ self.uyb_after_sumadd_sub_by_2_switch[1]
                        else:
                            self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carry_ogb_by_2_add[1] ^ self.uyb_after_sum_ogb_by_2_add[1]
                            self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carry_ogb_by_2_add_sub[1] ^ self.uyb_after_sum_ogb_by_2_add_sub[1]
                            self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carryadd_sub_ogb_by_2_switch[1] ^ self.uyb_after_sumadd_sub_ogb_by_2_switch[1]
                    else:
                        self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carryadd[1] ^ self.uyb_after_sumadd[1]
                        self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carryadd_sub[1] ^ self.uyb_after_sumadd_sub[1]
                        self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carryadd_sub_switch[1] ^ self.uyb_after_sumadd_sub_switch[1]

                else:
                    if self.shift_b_8_odd & self.a_minus_b_8:
                        if self.u_delta_update_sub_first_even:
                            self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carry_by_2_sub[1] ^ self.uyb_after_sum_by_2_sub[1]
                            self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carry_by_2_sub_sub[1] ^ self.uyb_after_sum_by_2_sub_sub[1]
                            self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carrysub_sub_by_2_switch[1] ^ self.uyb_after_sumsub_sub_by_2_switch[1]
                        else:
                            self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carry_ogb_by_2_sub[1] ^ self.uyb_after_sum_ogb_by_2_sub[1]
                            self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carry_ogb_by_2_sub_sub[1] ^ self.uyb_after_sum_ogb_by_2_sub_sub[1]
                            self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carrysub_sub_ogb_by_2_switch[1] ^ self.uyb_after_sumsub_sub_ogb_by_2_switch[1]
                    else:
                        self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carrysub[1] ^ self.uyb_after_sumsub[1]
                        self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carrysub_sub[1] ^ self.uyb_after_sumsub_sub[1]
                        self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carrysub_sub_switch[1] ^ self.uyb_after_sumsub_sub_switch[1]
            else:
                self.inv_u_y_ogb_after_lsb_2 = 0
                self.inv_u_y_ogb_after_lsb_2_sub = 0
                self.inv_u_y_ogb_after_lsb_2_sub_switch = 0
        else:
            self.inv_u_y_ogb_after_lsb_2 = 0
            self.inv_u_y_ogb_after_lsb_2_sub = 0
            self.inv_u_y_ogb_after_lsb_2_sub_switch = 0

    @always_comb
    def set_inv_u_y_ogb_after_lsb_2_sub(self):
        if ~self.done:
            if ~self.a_lsb:
                if self.shift_a_4 & ~self.a_lsb_2:
                    if self.shift_a_8 & ~self.a_lsb_3:
                        if ~self.u_after_lsb_3 & ~self.u_after_lsb_2 & ~self.u_after_lsb:
                            self.inv_u_y_ogb_after_lsb_2 = self.uyb_8_after_carry1[1] & self.uyb_8_after_sum1[1]
                            self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_8_after_sub_carry1[1] & self.uyb_8_after_sub_sum1[1]
                            self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uy_after_sub_switch_carry_8_1[1] & self.uy_after_sub_switch_sum_8_1[1]
                        elif ~self.u_after_lsb_2 & ~self.u_after_lsb:
                            self.inv_u_y_ogb_after_lsb_2 = self.uyb_8_after_carry2[1] & self.uyb_8_after_sum2[1]
                            self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_8_after_sub_carry2[1] & self.uyb_8_after_sub_sum2[1]
                            self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uy_after_sub_switch_carry_8_2[1] & self.uy_after_sub_switch_sum_8_2[1]
                        elif ~self.u_after_lsb:
                            if self.inv_u_ogb2_lsb_3:
                                self.inv_u_y_ogb_after_lsb_2 = self.uyb_8_after_carry3[1] & self.uyb_8_after_sum3[1]
                                self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_8_after_sub_carry3[1] & self.uyb_8_after_sub_sum3[1]
                                self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uy_after_sub_switch_carry_8_3[1] & self.uy_after_sub_switch_sum_8_3[1]
                            else:
                                self.inv_u_y_ogb_after_lsb_2 = self.uyb_8_after_carry4[1] & self.uyb_8_after_sum4[1]
                                self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_8_after_sub_carry4[1] & self.uyb_8_after_sub_sum4[1]
                                self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uy_after_sub_switch_carry_8_4[1] & self.uy_after_sub_switch_sum_8_4[1]
                        else:
                            if self.inv_u_ogb_after_lsb_3 & self.inv_u_ogb_after_lsb_2:
                                self.inv_u_y_ogb_after_lsb_2 = self.uyb_8_after_carry5[1] & self.uyb_8_after_sum5[1]
                                self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_8_after_sub_carry5[1] & self.uyb_8_after_sub_sum5[1]
                                self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uy_after_sub_switch_carry_8_5[1] & self.uy_after_sub_switch_sum_8_5[1]
                            elif self.inv_u_ogb_after_lsb_2:
                                self.inv_u_y_ogb_after_lsb_2 = self.uyb_8_after_carry6[1] & self.uyb_8_after_sum6[1]
                                self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_8_after_sub_carry6[1] & self.uyb_8_after_sub_sum6[1]
                                self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uy_after_sub_switch_carry_8_6[1] & self.uy_after_sub_switch_sum_8_6[1]
                            else:
                                if self.inv_u_ogb3_lsb_3:
                                    self.inv_u_y_ogb_after_lsb_2 = self.uyb_8_after_carry7[1] & self.uyb_8_after_sum7[1]
                                    self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_8_after_sub_carry7[1] & self.uyb_8_after_sub_sum7[1]
                                    self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uy_after_sub_switch_carry_8_7[1] & self.uy_after_sub_switch_sum_8_7[1]
                                else:
                                    self.inv_u_y_ogb_after_lsb_2 = self.uyb_8_after_carry8[1] & self.uyb_8_after_sum8[1]
                                    self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_8_after_sub_carry8[1] & self.uyb_8_after_sub_sum8[1]
                                    self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uy_after_sub_switch_carry_8_8[1] & self.uy_after_sub_switch_sum_8_8[1]
                    elif ~self.u_after_lsb_2 & ~self.u_after_lsb:
                        self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carry1[1] & self.uyb_after_sum1[1]
                        self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carry1_sub[1] & self.uyb_after_sum1_sub[1]
                        self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carry1_sub_switch[1] & self.uyb_after_sum1_sub_switch[1]
                    elif ~self.u_after_lsb:
                        self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carry2[1] & self.uyb_after_sum2[1]
                        self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carry2_sub[1] & self.uyb_after_sum2_sub[1]
                        self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carry2_sub_switch[1] & self.uyb_after_sum2_sub_switch[1]
                    elif self.inv_u_ogb_after_lsb_2:
                        self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carry3[1] & self.uyb_after_sum3[1]
                        self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carry3_sub[1] & self.uyb_after_sum3_sub[1]
                        self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carry3_sub_switch[1] & self.uyb_after_sum3_sub_switch[1]
                    else:
                        self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carry4[1] & self.uyb_after_sum4[1]
                        self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carry4_sub[1] & self.uyb_after_sum4_sub[1]
                        self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carry4_sub_switch[1] & self.uyb_after_sum4_sub_switch[1]
                elif self.u_after_lsb:
                    self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carry5[1] & self.uyb_after_sum5[1]
                    self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carry5_sub[1] & self.uyb_after_sum5_sub[1]
                    self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carry5_sub_switch[1] & self.uyb_after_sum5_sub_switch[1]
                    
                else:
                    self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carry6[1] & self.uyb_after_sum6[1]
                    self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carry6_sub[1] & self.uyb_after_sum6_sub[1]
                    self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carry6_sub_switch[1] & self.uyb_after_sum6_sub_switch[1]
            elif self.b_lsb & self.delta_sign:
                if self.shift_b_2_odd:
                    self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carrysub[1] & self.uyb_after_sumsub[1]
                    self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carrysub_sub[1] & self.uyb_after_sumsub_sub[1]
                    self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carrysub_sub_switch[1] & self.uyb_after_sumsub_sub_switch[1]
                if self.a_plus_b_4:
                    if self.shift_b_8_odd & self.a_plus_b_8:
                        if self.u_delta_update_add_even:
                            self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carry_by_2_add[1] & self.uyb_after_sum_by_2_add[1]
                            self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carry_by_2_add_sub[1] & self.uyb_after_sum_by_2_add_sub[1]
                            self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carryadd_sub_by_2_switch[1] & self.uyb_after_sumadd_sub_by_2_switch[1]
                        else:
                            self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carry_ogb_by_2_add[1] & self.uyb_after_sum_ogb_by_2_add[1]
                            self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carry_ogb_by_2_add_sub[1] & self.uyb_after_sum_ogb_by_2_add_sub[1]
                            self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carryadd_sub_ogb_by_2_switch[1] & self.uyb_after_sumadd_sub_ogb_by_2_switch[1]
                    else:
                        self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carryadd[1] & self.uyb_after_sumadd[1]
                        self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carryadd_sub[1] & self.uyb_after_sumadd_sub[1]
                        self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carryadd_sub_switch[1] & self.uyb_after_sumadd_sub_switch[1]
                else:
                    if self.shift_b_8_odd & self.a_minus_b_8:
                        if self.u_delta_update_sub_first_even:
                            self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carry_by_2_sub[1] & self.uyb_after_sum_by_2_sub[1]
                            self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carry_by_2_sub_sub[1] & self.uyb_after_sum_by_2_sub_sub[1]
                            self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carrysub_sub_by_2_switch[1] & self.uyb_after_sumsub_sub_by_2_switch[1]
                        else:
                            self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carry_ogb_by_2_sub[1] & self.uyb_after_sum_ogb_by_2_sub[1]
                            self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carry_ogb_by_2_sub_sub[1] & self.uyb_after_sum_ogb_by_2_sub_sub[1]
                            self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carrysub_sub_ogb_by_2_switch[1] & self.uyb_after_sumsub_sub_ogb_by_2_switch[1]
                    else:
                        self.inv_u_y_ogb_after_lsb_2 = self.uyb_after_carrysub[1] & self.uyb_after_sumsub[1]
                        self.inv_u_y_ogb_after_lsb_2_sub = self.uyb_after_carrysub_sub[1] & self.uyb_after_sumsub_sub[1]
                        self.inv_u_y_ogb_after_lsb_2_sub_switch = self.uyb_after_carrysub_sub_switch[1] & self.uyb_after_sumsub_sub_switch[1]
            else:
                self.inv_u_y_ogb_after_lsb_2 = 0
                self.inv_u_y_ogb_after_lsb_2_sub = 0
                self.inv_u_y_ogb_after_lsb_2_sub_switch = 0
        else:
            self.inv_u_y_ogb_after_lsb_2 = 0
            self.inv_u_y_ogb_after_lsb_2_sub = 0
            self.inv_u_y_ogb_after_lsb_2_sub_switch = 0

    @always_ff((posedge, "clk"))
    def set_debug_case(self):
        if ~self.done:
            if ~self.a_lsb:
                if self.shift_a_4 & ~self.a_lsb_2:
                    if self.shift_a_8 & ~self.a_lsb_3:
                        if ~self.u_after_lsb_3 & ~self.u_after_lsb_2 & ~self.u_after_lsb:
                            self.debug_case = 1
                        elif ~self.u_after_lsb_2 & ~self.u_after_lsb:
                            self.debug_case = 2
                        elif ~self.u_after_lsb:
                            if self.inv_u_ogb2_lsb_3:
                                self.debug_case = 3
                            else:
                                self.debug_case = 4
                        else:
                            if self.inv_u_ogb_after_lsb_3 & self.inv_u_ogb_after_lsb_2:
                                self.debug_case = 5
                            elif self.inv_u_ogb_after_lsb_2:
                                self.debug_case = 6
                            else:
                                if self.inv_u_ogb3_lsb_3:
                                    self.debug_case = 7
                                else:
                                    self.debug_case = 8
                    elif ~self.u_after_lsb_2 & ~self.u_after_lsb:
                        self.debug_case = 9
                    elif ~self.u_after_lsb:
                        self.debug_case = 10
                    elif self.inv_u_ogb_after_lsb_2:
                        self.debug_case = 11
                    else:
                        self.debug_case = 12
                elif self.u_after_lsb:
                    self.debug_case = 13
                else:
                    self.debug_case = 14
            elif self.b_lsb & self.delta_sign:
                if self.shift_b_2_odd:
                    if self.u_l:
                        self.debug_case = 15
                    else:
                        self.debug_case = 16
                elif self.a_plus_b_4:
                    if self.shift_b_8_odd & self.a_plus_b_8:
                        if self.u_delta_update_add_even:
                            if self.u_l:
                                self.debug_case = 17
                            else:
                                self.debug_case = 18
                        else:
                            if self.u_l:
                                self.debug_case = 19

                            else:
                                self.debug_case = 20
                    else:
                        if self.u_l:
                            self.debug_case = 21
                        else:
                            self.debug_case = 22
                else:
                    if self.shift_b_8_odd & self.a_minus_b_8:
                        if self.u_delta_update_sub_first_even:
                            if self.u_l:
                                self.debug_case = 23
                            else:
                                self.debug_case = 24
                        else:
                            if self.u_l:
                                self.debug_case = 25
                            else:
                                self.debug_case = 26
                    else:
                        if self.u_l:
                            self.debug_case = 27
                        else:
                            self.debug_case = 28
            # variable is not updated
            else:
                self.debug_case = 29
        else:
            self.debug_case = 0


if __name__ == "__main__":

    inter_bit_length = 1028
    
    u_csa_bezout_inter = Update_Bezout(inter_bit_length=inter_bit_length,
                                        add_og_val=True, 
                                        initial_0=False, 
                                        u_l=True, 
                                        u_y=True)

    verilog(u_csa_bezout_inter, filename="Update_Bezout_u.v")

    l_csa_bezout_inter = Update_Bezout(inter_bit_length=inter_bit_length, 
                                        add_og_val=False, 
                                        initial_0=True, 
                                        u_l=True, 
                                        u_y=False)

    verilog(l_csa_bezout_inter, filename="Update_Bezout_l.v")

    y_csa_bezout_inter = Update_Bezout(inter_bit_length=inter_bit_length,
                                        add_og_val=True, 
                                        initial_0=True, 
                                        u_l=False, 
                                        u_y=True)

    verilog(y_csa_bezout_inter, filename="Update_Bezout_y.v")

    n_csa_bezout_inter = Update_Bezout(inter_bit_length=inter_bit_length, 
                                        add_og_val=False, 
                                        initial_0=False, 
                                        u_l=False, 
                                        u_y=False)

    verilog(n_csa_bezout_inter, filename="Update_Bezout_n.v")
import kratos
from kratos import *

from xgcd.hardware.csa import *


class UpdateBezoutOdd(Generator):
    def __init__(self,
                 bit_length,
                 sub,
                 first_sub,
                 add_og_val,
                 testing=False,
                 DW=True,
                 debug_print=False):
        super().__init__(f"UpdateBezoutOdd", debug=True)

        self.inter_bit_length = bit_length
        self.sub = sub
        self.first_sub = first_sub
        self.add_og_val = add_og_val
        self.DW = DW
        self.debug_print = debug_print

        self.og_b = self.input("og_b", self.inter_bit_length)
        self.og_b2 = self.input("og_b2", self.inter_bit_length)
        self.og_b3 = self.input("og_b3", self.inter_bit_length)
        
        self.u_carry_in = self.input("u_carry_in", self.inter_bit_length)
        self.u_sum_in = self.input("u_sum_in", self.inter_bit_length)
        self.y_carry_in = self.input("y_carry_in", self.inter_bit_length)
        self.y_sum_in = self.input("y_sum_in", self.inter_bit_length)

        self.u_y_after_lsb = self.input("u_y_after_lsb", 1)
        self.u_y_after_lsb_2 = self.input("u_y_after_lsb_2", 1)

        self.inv_u_y_ogb_lsb_2_after = self.input("inv_u_y_ogb_lsb_2_after", 1)

        self.shift_b_2_odd = self.input("shift_b_2_odd", 1)

        self.u_carry = self.output("u_carry", self.inter_bit_length)
        self.u_sum = self.output("u_sum", self.inter_bit_length)

        self.u_y_first_carry = self.var("u_y_first_carry", self.inter_bit_length)
        self.u_y_first_sum = self.var("u_y_first_sum", self.inter_bit_length)
        self.u_y_second_carry = self.var("u_y_second_carry", self.inter_bit_length)
        self.u_y_second_sum = self.var("u_y_second_sum", self.inter_bit_length)

        if self.sub and not self.first_sub:
            self.wire(self.u_y_first_carry, self.y_carry_in)
            self.wire(self.u_y_first_sum, self.y_sum_in)
            self.wire(self.u_y_second_carry, self.u_carry_in)
            self.wire(self.u_y_second_sum, self.u_sum_in)
        else:
            self.wire(self.u_y_first_carry, self.u_carry_in)
            self.wire(self.u_y_first_sum, self.u_sum_in)
            self.wire(self.u_y_second_carry, self.y_carry_in)
            self.wire(self.u_y_second_sum, self.y_sum_in)

        self.ci = self.var("ci", 1)
        self.og_b_csa = self.var("og_b_csa", self.inter_bit_length)
        self.og_b2_csa = self.var("og_b2_csa", self.inter_bit_length)
        self.og_b3_csa = self.var("og_b3_csa", self.inter_bit_length)

        if self.add_og_val:
            self.wire(self.ci, const(0, 1))
            self.wire(self.og_b_csa, self.og_b)
            self.wire(self.og_b2_csa, self.og_b2)
            self.wire(self.og_b3_csa, self.og_b3)
        else:
            self.wire(self.ci, const(1, 1))
            self.wire(self.og_b_csa, ~self.og_b)
            self.wire(self.og_b2_csa, ~self.og_b2)
            self.wire(self.og_b3_csa, ~self.og_b3)

        # u + y
        self.u_y_carry = self.var("u_y_carry", self.inter_bit_length)
        self.u_y_sum = self.var("u_y_sum", self.inter_bit_length)

        u_y_csa = DW01_csa_4(self.inter_bit_length, (not self.sub), DW=self.DW)
        self.add_child("u_y_csa",
                        u_y_csa,
                        a_carry=self.u_y_first_carry,
                        a_sum=self.u_y_first_sum,
                        b_carry=self.u_y_second_carry,
                        b_sum=self.u_y_second_sum,
                        final_out_carry=self.u_y_carry,
                        final_out_sum=self.u_y_sum)
        
        # (u + y) // 2
        self.u_y_carry_by_2 = self.var("u_y_carry_by_2", self.inter_bit_length)
        self.u_y_sum_by_2 = self.var("u_y_sum_by_2", self.inter_bit_length)

        shiftu_y_2 = DW01_csa_shift_only(self.inter_bit_length)
        self.add_child("shiftu_y_2",
                       shiftu_y_2,
                       final_out_carry=self.u_y_carry,
                       final_out_sum=self.u_y_sum,
                       shifted_out_carry=self.u_y_carry_by_2,
                       shifted_out_sum=self.u_y_sum_by_2)
        
        # (u + y) // 4
        self.u_y_carry_by_4 = self.var("u_y_carry_by_4", self.inter_bit_length)
        self.u_y_sum_by_4 = self.var("u_y_sum_by_4", self.inter_bit_length)

        shiftu_y_4 = DW01_csa_shift_only_4(self.inter_bit_length)
        self.add_child("shiftu_y_4",
                       shiftu_y_4,
                       final_out_carry=self.u_y_carry,
                       final_out_sum=self.u_y_sum,
                       shifted_out_carry=self.u_y_carry_by_4,
                       shifted_out_sum=self.u_y_sum_by_4)
        
        # ((u + y) // 2 + og_b) // 2 = ((u + y) + 2 * og_b) // 4
        self.u_y_ogb2_carry = self.var("u_y_ogb2_carry", self.inter_bit_length)
        self.u_y_ogb2_sum = self.var("u_y_ogb2_sum", self.inter_bit_length)

        csa_u_y_ogb2 = DW01_csa(self.inter_bit_length, DW=self.DW)
        csa_u_y_ogb2.width.value = self.inter_bit_length
        self.add_child("csa_u_y_ogb2", 
                       csa_u_y_ogb2,
                       a=self.u_y_carry,
                       b=self.u_y_sum,
                       c=self.og_b2_csa,
                       ci=self.ci,
                       carry=self.u_y_ogb2_carry,
                       sum=self.u_y_ogb2_sum)
        
        self.u_y_ogb2_carry_by_4 = self.var("u_y_ogb2_carry_by_4", self.inter_bit_length)
        self.u_y_ogb2_sum_by_4 = self.var("u_y_ogb2_sum_by_4", self.inter_bit_length)

        shiftu_y_ogb2_by_4 = DW01_csa_shift_only_4(self.inter_bit_length)
        self.add_child("shiftu_y_ogb2_by_4",
                       shiftu_y_ogb2_by_4,
                       final_out_carry=self.u_y_ogb2_carry,
                       final_out_sum=self.u_y_ogb2_sum,
                       shifted_out_carry=self.u_y_ogb2_carry_by_4,
                       shifted_out_sum=self.u_y_ogb2_sum_by_4)

        # (u + y) + og_b
        self.u_y_ogb_carry = self.var("u_y_ogb_carry", self.inter_bit_length)
        self.u_y_ogb_sum = self.var("u_y_ogb_sum", self.inter_bit_length)

        csa_u_y_ogb = DW01_csa(self.inter_bit_length, DW=self.DW)
        csa_u_y_ogb.width.value = self.inter_bit_length
        self.add_child("csa_u_y_ogb", 
                       csa_u_y_ogb,
                       a=self.u_y_carry,
                       b=self.u_y_sum,
                       c=self.og_b_csa,
                       ci=self.ci,
                       carry=self.u_y_ogb_carry,
                       sum=self.u_y_ogb_sum)

        self.inv_u_y_ogb_lsb_2 = self.var("inv_u_y_ogb_lsb_2", 1)
        # in DW CSA, carry[0] = c[0] and since og_b_csa is always odd, carry[0] = 1 always
        # unless it is subtraction in which case we invert and carry[0] = 0 always
        if self.add_og_val:
            self.wire(self.inv_u_y_ogb_lsb_2, self.u_y_ogb_carry[1] ^ self.u_y_ogb_sum[1])
        else:
            self.wire(self.inv_u_y_ogb_lsb_2, self.u_y_ogb_carry[1] & self.u_y_ogb_sum[1])

        # (u + y + og_b) // 2
        self.u_y_ogb_carry_by_2 = self.var("u_y_ogb_carry_by_2", self.inter_bit_length)
        self.u_y_ogb_sum_by_2 = self.var("u_y_ogb_sum_by_2", self.inter_bit_length)

        shiftu_y_ogb_by_2 = DW01_csa_shift_only(self.inter_bit_length)
        self.add_child("shiftu_y_ogb_by_2",
                       shiftu_y_ogb_by_2,
                       final_out_carry=self.u_y_ogb_carry,
                       final_out_sum=self.u_y_ogb_sum,
                       shifted_out_carry=self.u_y_ogb_carry_by_2,
                       shifted_out_sum=self.u_y_ogb_sum_by_2)
        
        # (u + y + og_b) // 4
        self.u_y_ogb_carry_by_4 = self.var("u_y_ogb_carry_by_4", self.inter_bit_length)
        self.u_y_ogb_sum_by_4 = self.var("u_y_ogb_sum_by_4", self.inter_bit_length)

        shiftu_y_ogb_by_4 = DW01_csa_shift_only_4(self.inter_bit_length)
        self.add_child("shiftu_y_ogb_by_4",
                       shiftu_y_ogb_by_4,
                       final_out_carry=self.u_y_ogb_carry,
                       final_out_sum=self.u_y_ogb_sum,
                       shifted_out_carry=self.u_y_ogb_carry_by_4,
                       shifted_out_sum=self.u_y_ogb_sum_by_4)

        # (((u + y) + og_b) // 2 + og_b) // 2 = ((u + y) + 3 * og_b) // 4
        self.u_y_ogb3_carry = self.var("u_y_ogb3_carry", self.inter_bit_length)
        self.u_y_ogb3_sum = self.var("u_y_ogb3_sum", self.inter_bit_length)

        csa_u_y_ogb3 = DW01_csa(self.inter_bit_length, DW=self.DW)
        csa_u_y_ogb3.width.value = self.inter_bit_length
        self.add_child("csa_u_y_ogb3", 
                       csa_u_y_ogb3,
                       a=self.u_y_carry,
                       b=self.u_y_sum,
                       c=self.og_b3_csa,
                       ci=self.ci,
                       carry=self.u_y_ogb3_carry,
                       sum=self.u_y_ogb3_sum)

        self.u_y_ogb3_by4_carry = self.var("u_y_ogb3_by4_carry", self.inter_bit_length)
        self.u_y_ogb3_by4_sum = self.var("u_y_ogb3_by4_sum", self.inter_bit_length)

        shiftu_y_ogb3_by4 = DW01_csa_shift_only_4(self.inter_bit_length)
        self.add_child("shiftu_y_ogb3_by4",
                       shiftu_y_ogb3_by4,
                       final_out_carry=self.u_y_ogb3_carry,
                       final_out_sum=self.u_y_ogb3_sum,
                       shifted_out_carry=self.u_y_ogb3_by4_carry,
                       shifted_out_sum=self.u_y_ogb3_by4_sum)

        self.u_y_after_lsb_2_used = self.var("u_y_after_lsb_2_used", 1)
        if testing:
            self.wire(self.u_y_after_lsb_2_used, ((self.u_y_carry + self.u_y_sum) % 4 == 0))
        else:
            self.wire(self.u_y_after_lsb_2_used, ~self.u_y_after_lsb_2)
        
        if self.debug_print:
            self.odd_case = self.var("odd_case", 4)
            self.u_y_after_lsb_2_true = self.var("u_y_after_lsb_2_true", 1)
            self.wire(self.u_y_after_lsb_2_true, (self.u_y_carry + self.u_y_sum) % 4 == 0)

        self.add_code(self.set_u_l_out)

    @always_comb
    def set_u_l_out(self):
        # reducing one bit -- factor of 2
        if self.shift_b_2_odd:
            if self.u_y_after_lsb:
                self.u_carry = self.u_y_ogb_carry_by_2
                self.u_sum = self.u_y_ogb_sum_by_2
                if self.debug_print:
                    self.odd_case = 5
            else:
                self.u_carry = self.u_y_carry_by_2
                self.u_sum = self.u_y_sum_by_2
                if self.debug_print:
                    self.odd_case = 6

        # reducing two bits -- factor of 4
        # (u + y) // 4, add og_b as needed
        # if u + y is odd
        elif self.u_y_after_lsb:
            # if u + y is odd, add u + y + og_b to make even
            # if u + y + og_b is divisible by 4
            if self.inv_u_y_ogb_lsb_2:
                self.u_carry = self.u_y_ogb_carry_by_4
                self.u_sum = self.u_y_ogb_sum_by_4
                if self.debug_print:
                    self.odd_case = 1
            # if u + y + og_b is not divisible by 4
            else:
                self.u_carry = self.u_y_ogb3_by4_carry
                self.u_sum = self.u_y_ogb3_by4_sum
                if self.debug_print:
                    self.odd_case = 2
        # u + y is divisible by 4
        elif self.u_y_after_lsb_2_used:
            self.u_carry = self.u_y_carry_by_4
            self.u_sum = self.u_y_sum_by_4
            if self.debug_print:
                    self.odd_case = 3
        # u + y is divisible by 2 but not 4, add og_b to make
        # even and then divide by 2
        else:
            self.u_carry = self.u_y_ogb2_carry_by_4
            self.u_sum = self.u_y_ogb2_sum_by_4
            if self.debug_print:
                    self.odd_case = 4


if __name__ == "__main__":
    dut = UpdateBezoutOdd(1028, True, True, False)
    verilog(dut, filename="UpdateBezoutOdd.v")
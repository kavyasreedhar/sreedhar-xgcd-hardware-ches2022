import kratos
from kratos import *

from xgcd.hardware.csa import *


class Update_a_b_odd(Generator):
    def __init__(self,
                 bit_length,
                 sub,
                 switch_inputs,
                 DW=True,
                 debug_print=False):
        super().__init__(f"Update_a_b_odd_{bit_length}", debug=True)

        self.inter_bit_length = bit_length
        self.sub = sub
        self.switch_inputs = switch_inputs
        self.DW = DW
        self.debug_print = debug_print

        if self.debug_print:
            self.clk = self.clock("clk")
            self.rst_n = self.reset("rst_n", 1)
            
        self.inter_bit_length_msb = self.inter_bit_length - 1

        self.a_carry = self.input("a_carry", self.inter_bit_length)
        self.b_carry = self.input("b_carry", self.inter_bit_length)
        self.a_sum = self.input("a_sum", self.inter_bit_length)
        self.b_sum = self.input("b_sum", self.inter_bit_length)

        self.a_out_carry = self.output("a_out_carry", self.inter_bit_length)
        self.a_out_sum = self.output("a_out_sum", self.inter_bit_length)
        self.a_out_carry_by_8 = self.output("a_out_carry_by_8", self.inter_bit_length)
        self.a_out_sum_by_8 = self.output("a_out_sum_by_8", self.inter_bit_length)
        self.a_out_carry_preshift_out = self.output("a_out_carry_preshift_out", self.inter_bit_length)
        self.a_out_sum_preshift_out = self.output("a_out_sum_preshift_out", self.inter_bit_length)

        self.a_out_carry_preshift = self.var("a_out_carry_preshift", self.inter_bit_length)
        self.a_out_sum_preshift = self.var("a_out_sum_preshift", self.inter_bit_length)
        self.wire(self.a_out_carry_preshift_out, self.a_out_carry_preshift)
        self.wire(self.a_out_sum_preshift_out, self.a_out_sum_preshift)

        if debug_print:
            self.a_out = self.output("a_out", self.inter_bit_length)
            self.wire(self.a_out, self.a_out_carry + self.a_out_sum)

        self.first_carry = self.var("first_carry", self.inter_bit_length)
        self.first_sum = self.var("first_sum", self.inter_bit_length)
        self.second_carry = self.var("second_carry", self.inter_bit_length)
        self.second_sum = self.var("second_sum", self.inter_bit_length)

        if self.sub and not self.switch_inputs:
            self.wire(self.first_carry, self.b_carry)
            self.wire(self.first_sum, self.b_sum)
            self.wire(self.second_carry, self.a_carry)
            self.wire(self.second_sum, self.a_sum)
        else:
            self.wire(self.first_carry, self.a_carry)
            self.wire(self.first_sum, self.a_sum)
            self.wire(self.second_carry, self.b_carry)
            self.wire(self.second_sum, self.b_sum)

        a_b_csa = DW01_csa_4(self.inter_bit_length, (not self.sub), DW=self.DW)
        self.add_child("a_b_csa",
                        a_b_csa,
                        a_carry=self.first_carry,
                        a_sum=self.first_sum,
                        b_carry=self.second_carry,
                        b_sum=self.second_sum,
                        final_out_carry=self.a_out_carry_preshift,
                        final_out_sum=self.a_out_sum_preshift)

        a_b_shift_by_4 = DW01_csa_shift_only_4(self.inter_bit_length)
        self.add_child("a_b_shift_by_4",
                        a_b_shift_by_4,
                        final_out_carry=self.a_out_carry_preshift,
                        final_out_sum=self.a_out_sum_preshift,
                        shifted_out_carry=self.a_out_carry,
                        shifted_out_sum=self.a_out_sum)
        
        a_b_shift_by_8 = DW01_csa_shift_only_8(self.inter_bit_length)
        self.add_child("a_b_shift_by_8",
                        a_b_shift_by_8,
                        final_out_carry=self.a_out_carry_preshift,
                        final_out_sum=self.a_out_sum_preshift,
                        shifted_out_carry=self.a_out_carry_by_8,
                        shifted_out_sum=self.a_out_sum_by_8)
                        

if __name__ == "__main__":
    dut = Update_a_b_odd(804, False, False, True)
    verilog(dut, filename="Update_a_b_odd.v")

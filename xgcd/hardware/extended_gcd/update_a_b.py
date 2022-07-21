import kratos
from kratos import *

from xgcd.hardware.csa import *
from xgcd.hardware.extended_gcd.update_a_b_odd import Update_a_b_odd

class Update_a_b(Generator):
    def __init__(self,
                 bit_length,
                 inter_bit_length,
                 delta_msb,
                 DW=True,
                 debug_print=False):
        super().__init__(f"Update_a_b_{inter_bit_length}", debug=True)

        self.bit_length = bit_length
        self.inter_bit_length = inter_bit_length
        self.delta_msb = delta_msb
        self.DW = DW
        self.debug_print = debug_print
        
        self.clk = self.clock("clk")
        self.rst_n = self.reset("rst_n", 1)

        self.internal_start = self.input("internal_start", 1)
        self.compute = self.input("compute", 1)

        self.A = self.input("A", self.bit_length)
        self.B = self.input("B", self.bit_length)

        self.delta = self.input("delta", self.delta_msb + 1, is_signed=True)

        # reduction factor signals
        self.shift_a_4 = self.input("shift_a_4", 1)
        self.shift_b_4 = self.input("shift_b_4", 1)
        self.shift_a_8 = self.input("shift_a_8", 1)
        self.shift_b_8 = self.input("shift_b_8", 1)
        self.shift_b_2_odd = self.input("shift_b_2_odd", 1)
        self.shift_b_8_odd = self.input("shift_b_8_odd", 1)

        self.even_case = self.output("even_case", 2)

        self.a_carry_out = self.output("a_carry_out", self.inter_bit_length)
        self.b_carry_out = self.output("b_carry_out", self.inter_bit_length)
        self.a_sum_out = self.output("a_sum_out", self.inter_bit_length)
        self.b_sum_out = self.output("b_sum_out", self.inter_bit_length)

        # a, b, a + b divisibility control signals
        self.a_after_lsb_out = self.output("a_after_lsb_out", 1)
        self.b_after_lsb_out = self.output("b_after_lsb_out", 1)
        self.a_after_lsb_2_out = self.output("a_after_lsb_2_out", 1)
        self.b_after_lsb_2_out = self.output("b_after_lsb_2_out", 1)
        self.a_after_lsb_3_out = self.output("a_after_lsb_3_out", 1)
        self.b_after_lsb_3_out = self.output("b_after_lsb_3_out", 1)
        self.ab_after_lsb_2_out = self.output("ab_after_lsb_2_out", 1)
        self.ab_after_lsb_3_out = self.output("ab_after_lsb_3_out", 1)
        self.a_minus_b_after_lsb_3_out = self.output("a_minus_b_after_lsb_3_out", 1)

        self.a_carry = self.var("a_carry", self.inter_bit_length)
        self.b_carry = self.var("b_carry", self.inter_bit_length)
        self.a_sum = self.var("a_sum", self.inter_bit_length)
        self.b_sum = self.var("b_sum", self.inter_bit_length)

        self.a_carry_comb = self.var("a_carry_comb", self.inter_bit_length)
        self.b_carry_comb = self.var("b_carry_comb", self.inter_bit_length)
        self.a_sum_comb = self.var("a_sum_comb", self.inter_bit_length)
        self.b_sum_comb = self.var("b_sum_comb", self.inter_bit_length)

        self.a_after_lsb = self.var("a_after_lsb", 1)
        self.b_after_lsb = self.var("b_after_lsb", 1)
        self.a_after_lsb_2 = self.var("a_after_lsb_2", 1)
        self.b_after_lsb_2 = self.var("b_after_lsb_2", 1)
        self.a_after_lsb_3 = self.var("a_after_lsb_3", 1)
        self.b_after_lsb_3 = self.var("b_after_lsb_3", 1)
        self.ab_after_lsb_2 = self.var("ab_after_lsb_2", 1)
        self.ab_after_lsb_3 = self.var("ab_after_lsb_3", 1)
        self.a_minus_b_after_lsb_3 = self.var("a_minus_b_after_lsb_3", 1)

        self.wire(self.a_carry_out, self.a_carry)
        self.wire(self.b_carry_out, self.b_carry)
        self.wire(self.a_sum_out, self.a_sum)
        self.wire(self.b_sum_out, self.b_sum)

        self.wire(self.a_after_lsb_out, self.a_after_lsb)
        self.wire(self.b_after_lsb_out, self.b_after_lsb)
        self.wire(self.a_after_lsb_2_out, self.a_after_lsb_2)
        self.wire(self.b_after_lsb_2_out, self.b_after_lsb_2)
        self.wire(self.a_after_lsb_3_out, self.a_after_lsb_3)
        self.wire(self.b_after_lsb_3_out, self.b_after_lsb_3)
        self.wire(self.ab_after_lsb_2_out, self.ab_after_lsb_2)
        self.wire(self.ab_after_lsb_3_out, self.ab_after_lsb_3)
        self.wire(self.a_minus_b_after_lsb_3_out, self.a_minus_b_after_lsb_3)

        self.a_delta_update_add_carry = self.var("a_delta_update_add_carry", self.inter_bit_length)
        self.a_delta_update_add_sum = self.var("a_delta_update_add_sum", self.inter_bit_length)

        self.a_out_carry_preshift = self.output("a_out_carry_preshift", self.inter_bit_length)
        self.a_out_sum_preshift = self.output("a_out_sum_preshift", self.inter_bit_length)

        self.a_b_carry_by_8 = self.var("a_b_carry_by_8", self.inter_bit_length)
        self.a_b_sum_by_8 = self.var("a_b_sum_by_8", self.inter_bit_length)

        delta_update_add = Update_a_b_odd(self.inter_bit_length, False, False, DW=self.DW)
        self.add_child("delta_update_add",
                       delta_update_add,
                       a_carry=self.a_carry,
                       a_sum=self.a_sum,
                       b_carry=self.b_carry,
                       b_sum=self.b_sum,
                       a_out_carry=self.a_delta_update_add_carry,
                       a_out_sum=self.a_delta_update_add_sum,
                       a_out_carry_by_8=self.a_b_carry_by_8,
                       a_out_sum_by_8=self.a_b_sum_by_8,
                       a_out_carry_preshift_out=self.a_out_carry_preshift,
                       a_out_sum_preshift_out=self.a_out_sum_preshift)
        
        self.a_delta_update_sub_first_carry = self.var("a_delta_update_sub_first_carry", self.inter_bit_length)
        self.a_delta_update_sub_first_sum = self.var("a_delta_update_sub_first_sum", self.inter_bit_length)

        self.a_minus_b_carry = self.var("a_minus_b_carry", self.inter_bit_length)
        self.a_minus_b_sum = self.var("a_minus_b_sum", self.inter_bit_length)

        delta_update_sub_first = Update_a_b_odd(self.inter_bit_length, True, True, DW=self.DW)
        self.add_child("delta_update_sub_first",
                       delta_update_sub_first,
                       a_carry=self.a_carry,
                       a_sum=self.a_sum,
                       b_carry=self.b_carry,
                       b_sum=self.b_sum,
                       a_out_carry=self.a_delta_update_sub_first_carry,
                       a_out_sum=self.a_delta_update_sub_first_sum,
                       a_out_carry_preshift_out=self.a_minus_b_carry,
                       a_out_sum_preshift_out=self.a_minus_b_sum)
        
        self.a_minus_b_by_2_carry = self.var("a_minus_b_by_2_carry", self.inter_bit_length)
        self.a_minus_b_by_2_sum = self.var("a_minus_b_by_2_sum", self.inter_bit_length)

        a_minus_b_2 = DW01_csa_shift_only(self.inter_bit_length)
        self.add_child("a_minus_b_2",
                       a_minus_b_2,
                       final_out_carry=self.a_minus_b_carry,
                       final_out_sum=self.a_minus_b_sum,
                       shifted_out_carry=self.a_minus_b_by_2_carry,
                       shifted_out_sum=self.a_minus_b_by_2_sum)
        
        self.a_delta_update_sub_first_carry_by_2 = self.var("a_delta_update_sub_first_carry_by_2", self.inter_bit_length)
        self.a_delta_update_sub_first_sum_by_2 = self.var("a_delta_update_sub_first_sum_by_2", self.inter_bit_length)

        shifta_delta_update_sub_first_carry = DW01_csa_shift_only(self.inter_bit_length)
        self.add_child("shifta_delta_update_sub_first_carry",
                       shifta_delta_update_sub_first_carry,
                       final_out_carry=self.a_delta_update_sub_first_carry,
                       final_out_sum=self.a_delta_update_sub_first_sum,
                       shifted_out_carry=self.a_delta_update_sub_first_carry_by_2,
                       shifted_out_sum=self.a_delta_update_sub_first_sum_by_2)

        # start if one number is even
        self.A_B_carry = self.var("A_B_carry", self.inter_bit_length)
        self.A_B_sum = self.var("A_B_sum", self.inter_bit_length)
        even_case_add = DW01_csa(self.inter_bit_length, DW=self.DW)
        even_case_add.width.value = self.inter_bit_length
        self.add_child("even_case_add", even_case_add,
                       a=self.A.extend(self.inter_bit_length),
                       b=self.B.extend(self.inter_bit_length),
                       c=const(0, self.inter_bit_length),
                       ci=const(0, 1),
                       carry=self.A_B_carry,
                       sum=self.A_B_sum)

        # divide by 2
        self.a_carry_by_2 = self.var("a_carry_by_2", self.inter_bit_length)
        self.a_sum_by_2 = self.var("a_sum_by_2", self.inter_bit_length)

        shifta = DW01_csa_shift_only(self.inter_bit_length)
        self.add_child("shifta",
                       shifta,
                       final_out_carry=self.a_carry,
                       final_out_sum=self.a_sum,
                       shifted_out_carry=self.a_carry_by_2,
                       shifted_out_sum=self.a_sum_by_2)
        
        self.b_carry_by_2 = self.var("b_carry_by_2", self.inter_bit_length)
        self.b_sum_by_2 = self.var("b_sum_by_2", self.inter_bit_length)
        
        shiftb = DW01_csa_shift_only(self.inter_bit_length)
        self.add_child("shiftb",
                       shiftb,
                       final_out_carry=self.b_carry,
                       final_out_sum=self.b_sum,
                       shifted_out_carry=self.b_carry_by_2,
                       shifted_out_sum=self.b_sum_by_2)
        
        # divide by 4
        self.a_carry_by_4 = self.var("a_carry_by_4", self.inter_bit_length)
        self.a_sum_by_4 = self.var("a_sum_by_4", self.inter_bit_length)

        shifta4 = DW01_csa_shift_only_4(self.inter_bit_length)
        self.add_child("shifta4",
                       shifta4,
                       final_out_carry=self.a_carry,
                       final_out_sum=self.a_sum,
                       shifted_out_carry=self.a_carry_by_4,
                       shifted_out_sum=self.a_sum_by_4)
        
        self.b_carry_by_4 = self.var("b_carry_by_4", self.inter_bit_length)
        self.b_sum_by_4 = self.var("b_sum_by_4", self.inter_bit_length)

        shiftb4 = DW01_csa_shift_only_4(self.inter_bit_length)
        self.add_child("shiftb4",
                       shiftb4,
                       final_out_carry=self.b_carry,
                       final_out_sum=self.b_sum,
                       shifted_out_carry=self.b_carry_by_4,
                       shifted_out_sum=self.b_sum_by_4)

        # divide by 8
        self.a_carry_by_8 = self.var("a_carry_by_8", self.inter_bit_length)
        self.a_sum_by_8 = self.var("a_sum_by_8", self.inter_bit_length)

        shifta8 = DW01_csa_shift_only_8(self.inter_bit_length)
        self.add_child("shifta8",
                       shifta8,
                       final_out_carry=self.a_carry,
                       final_out_sum=self.a_sum,
                       shifted_out_carry=self.a_carry_by_8,
                       shifted_out_sum=self.a_sum_by_8)
        
        self.b_carry_by_8 = self.var("b_carry_by_8", self.inter_bit_length)
        self.b_sum_by_8 = self.var("b_sum_by_8", self.inter_bit_length)

        shiftb8 = DW01_csa_shift_only_8(self.inter_bit_length)
        self.add_child("shiftb8",
                       shiftb8,
                       final_out_carry=self.b_carry,
                       final_out_sum=self.b_sum,
                       shifted_out_carry=self.b_carry_by_8,
                       shifted_out_sum=self.b_sum_by_8)

        self.ab_carry_a = self.var("ab_carry_a", 3)
        self.ab_sum_a = self.var("ab_sum_a", 3)

        # control signals
        ab_csa_a = DW01_csa_4(3, True, DW=self.DW)
        self.add_child("ab_csa_a",
                        ab_csa_a,
                        a_carry=self.a_carry_comb[2, 0],
                        a_sum=self.a_sum_comb[2, 0],
                        b_carry=self.b_carry[2, 0],
                        b_sum=self.b_sum[2, 0],
                        final_out_carry=self.ab_carry_a,
                        final_out_sum=self.ab_sum_a)
        
        self.a_minus_b_carry_a = self.var("a_minus_b_carry_a", 3)
        self.a_minus_b_sum_a = self.var("a_minus_b_sum_a", 3)

        a_minus_b_csa_a = DW01_csa_4(3, False, DW=self.DW)
        self.add_child("a_minus_b_csa_a",
                        a_minus_b_csa_a,
                        a_carry=self.a_carry_comb[2, 0],
                        a_sum=self.a_sum_comb[2, 0],
                        b_carry=self.b_carry[2, 0],
                        b_sum=self.b_sum[2, 0],
                        final_out_carry=self.a_minus_b_carry_a,
                        final_out_sum=self.a_minus_b_sum_a)

        self.ab_carry_b = self.var("ab_carry_b", 3)
        self.ab_sum_b = self.var("ab_sum_b", 3)

        ab_csa_b = DW01_csa_4(3, True, DW=self.DW)
        self.add_child("ab_csa_b",
                        ab_csa_b,
                        a_carry=self.a_carry[2, 0],
                        a_sum=self.a_sum[2, 0],
                        b_carry=self.b_carry_comb[2, 0],
                        b_sum=self.b_sum_comb[2, 0],
                        final_out_carry=self.ab_carry_b,
                        final_out_sum=self.ab_sum_b)

        self.a_minus_b_carry_b = self.var("a_minus_b_carry_b", 3)
        self.a_minus_b_sum_b = self.var("a_minus_b_sum_b", 3)

        a_minus_b_csa_b = DW01_csa_4(3, False, DW=self.DW)
        self.add_child("a_minus_b_csa_b",
                        a_minus_b_csa_b,
                        a_carry=self.a_carry[2, 0],
                        a_sum=self.a_sum[2, 0],
                        b_carry=self.b_carry_comb[2, 0],
                        b_sum=self.b_sum_comb[2, 0],
                        final_out_carry=self.a_minus_b_carry_b,
                        final_out_sum=self.a_minus_b_sum_b)
        
        self.add_code(self.set_a_signals)
        self.add_code(self.set_b_signals)
        self.add_code(self.set_ab_signals)
        self.add_code(self.set_even_case)
        self.add_code(self.set_a_comb)
        self.add_code(self.set_b_comb)


    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def set_even_case(self):
        if ~self.rst_n:
            self.even_case = 0
        elif self.internal_start:
            self.even_case = 0
            if ~self.A[0]:
                self.even_case = 1
            elif ~self.B[0]:
                self.even_case = 2

    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def set_b_signals(self):
        if ~self.rst_n:
            self.b_carry = 0
            self.b_sum = 0
            self.b_after_lsb = 0
            self.b_after_lsb_2 = 0
            self.b_after_lsb_3 = 0
        elif self.internal_start:
            self.b_carry = self.b_carry_comb
            self.b_sum = self.b_sum_comb
            self.b_after_lsb = 1
            self.b_after_lsb_2 = 1
            self.b_after_lsb_3 = 1
        elif ~(self.compute):
            if self.a_after_lsb & (~self.b_after_lsb | unsigned(self.delta[self.delta_msb])):
                self.b_carry = self.b_carry_comb
                self.b_sum = self.b_sum_comb
                self.b_after_lsb = self.b_carry_comb[0] ^ self.b_sum_comb[0]
                self.b_after_lsb_2 = self.b_carry_comb[1] ^ self.b_sum_comb[1] ^ self.b_carry_comb[0]
                self.b_after_lsb_3 = (self.b_carry_comb[1] | self.b_sum_comb[1]) ^ self.b_carry_comb[2] ^ self.b_sum_comb[2]

    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def set_a_signals(self):
        if ~self.rst_n:
            self.a_carry = 0
            self.a_sum = 0
            self.a_after_lsb = 0
            self.a_after_lsb_2 = 0
            self.a_after_lsb_3 = 0
        elif self.internal_start:
            self.a_carry = self.a_carry_comb
            self.a_sum = self.a_sum_comb
            self.a_after_lsb = 1
            self.a_after_lsb_2 = 1
            self.a_after_lsb_3 = 1
        elif ~(self.compute):
            if ~self.a_after_lsb | (self.b_after_lsb & unsigned(~self.delta[self.delta_msb])):
                self.a_carry = self.a_carry_comb
                self.a_sum = self.a_sum_comb
                self.a_after_lsb = self.a_carry_comb[0] ^ self.a_sum_comb[0]
                self.a_after_lsb_2 = self.a_carry_comb[1] ^ self.a_sum_comb[1] ^ self.a_carry_comb[0]
                self.a_after_lsb_3 = (self.a_carry_comb[1] | self.a_sum_comb[1]) ^ self.a_carry_comb[2] ^ self.a_sum_comb[2]
    
    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def set_ab_signals(self):
        if ~self.rst_n:
            self.ab_after_lsb_2 = 0
            self.ab_after_lsb_3 = 0
            self.a_minus_b_after_lsb_3 = 0
        elif self.internal_start:
            # both A and B are odd, so A + B is divisible by 4
            # only if A[1] ^ B[1] = 1
            self.ab_after_lsb_2 = self.A[1] ^ self.B[1]
            self.ab_after_lsb_3 = ~((self.A[1] | self.B[1]) ^ self.A[2] ^ self.B[2])
            self.a_minus_b_after_lsb_3 = (self.A[2, 0] - self.B[2, 0]) == 0
            if ~self.A[0]:
                self.ab_after_lsb_2 = self.A_B_carry[1] ^ self.A_B_sum[1] ^ self.B[1]
                self.ab_after_lsb_3 = (self.A_B_carry[2, 0] + self.A_B_sum[2, 0] + self.B[2, 0]) == 0
                self.a_minus_b_after_lsb_3 = (self.A_B_carry[2, 0] + self.A_B_sum[2, 0] - self.B[2, 0]) == 0
            elif ~self.B[0]:
                self.ab_after_lsb_2 = self.A_B_carry[1] ^ self.A_B_sum[1] ^ self.A[1]
                self.ab_after_lsb_3 = (self.A_B_carry[2, 0] + self.A_B_sum[2, 0] + self.A[2, 0]) == 0
                self.a_minus_b_after_lsb_3 = (self.A_B_carry[2, 0] + self.A_B_sum[2, 0] - self.A[2, 0]) == 0
        elif ~(self.compute):
            if ~self.a_after_lsb | (self.b_after_lsb & unsigned(~self.delta[self.delta_msb])):
                self.ab_after_lsb_2 = ~(self.ab_carry_a[1] ^ self.ab_sum_a[1] ^ self.ab_carry_a[0])
                # this is always nested within ab_after_lsb_2
                self.ab_after_lsb_3 = ~((self.ab_carry_a[1] | self.ab_sum_a[1]) ^ self.ab_carry_a[2] ^ self.ab_sum_a[2])
                self.a_minus_b_after_lsb_3 = ((self.a_minus_b_carry_a + self.a_minus_b_sum_a) == 0)
            else:
                self.ab_after_lsb_2 = ~(self.ab_carry_b[1] ^ self.ab_sum_b[1] ^ self.ab_carry_b[0])
                self.ab_after_lsb_3 = ~((self.ab_carry_b[1] | self.ab_sum_b[1]) ^ self.ab_carry_b[2] ^ self.ab_sum_b[2])
                self.a_minus_b_after_lsb_3 = ((self.a_minus_b_carry_b + self.a_minus_b_sum_b) == 0)

    @always_comb
    def set_a_comb(self):
        if self.internal_start:
            if ~self.A[0]:
                self.a_carry_comb = self.A_B_carry
                self.a_sum_comb = self.A_B_sum
            else:
                self.a_carry_comb = 0
                self.a_sum_comb = self.A.extend(self.inter_bit_length)
        elif ~self.compute:
            if self.shift_a_8 & ~self.a_after_lsb_3 & ~self.a_after_lsb_2 & ~self.a_after_lsb:
                self.a_carry_comb = self.a_carry_by_8
                self.a_sum_comb = self.a_sum_by_8
            elif self.shift_a_4 & ~self.a_after_lsb_2 & ~self.a_after_lsb:
                self.a_carry_comb = self.a_carry_by_4
                self.a_sum_comb = self.a_sum_by_4
            elif ~self.a_after_lsb:
                self.a_carry_comb = self.a_carry_by_2
                self.a_sum_comb = self.a_sum_by_2
            elif self.b_after_lsb & unsigned(~self.delta[self.delta_msb]):
                if self.shift_b_2_odd:
                    self.a_carry_comb = self.a_minus_b_by_2_carry
                    self.a_sum_comb = self.a_minus_b_by_2_sum
                # a + b divisible by 4
                elif self.ab_after_lsb_2:
                    # a + b divisible by 8
                    if self.shift_b_8_odd & self.ab_after_lsb_3:
                        self.a_carry_comb = self.a_b_carry_by_8
                        self.a_sum_comb = self.a_b_sum_by_8
                    else:
                        self.a_carry_comb = self.a_delta_update_add_carry
                        self.a_sum_comb = self.a_delta_update_add_sum
                # a - b divisible by 4
                else:
                    # a - b divisible by 8
                    if self.shift_b_8_odd & self.a_minus_b_after_lsb_3:
                        self.a_carry_comb = self.a_delta_update_sub_first_carry_by_2
                        self.a_sum_comb = self.a_delta_update_sub_first_sum_by_2
                    else:
                        self.a_carry_comb = self.a_delta_update_sub_first_carry
                        self.a_sum_comb = self.a_delta_update_sub_first_sum
            else:
                self.a_carry_comb = self.a_carry
                self.a_sum_comb = self.a_sum
        else:
            self.a_carry_comb = self.a_carry
            self.a_sum_comb = self.a_sum

    @always_comb
    def set_b_comb(self):
        if self.internal_start:
            if ~self.B[0]:
                self.b_carry_comb = self.A_B_carry
                self.b_sum_comb = self.A_B_sum
            else:
                self.b_carry_comb = 0
                self.b_sum_comb = self.B.extend(self.inter_bit_length)
        elif ~(self.compute) & self.a_after_lsb:
            if self.shift_b_8 & ~self.b_after_lsb_3 & ~self.b_after_lsb_2 & ~self.b_after_lsb:
                self.b_carry_comb = self.b_carry_by_8
                self.b_sum_comb = self.b_sum_by_8
            elif self.shift_b_4 & ~self.b_after_lsb_2 & ~self.b_after_lsb:
                self.b_carry_comb = self.b_carry_by_4
                self.b_sum_comb = self.b_sum_by_4
            elif ~self.b_after_lsb:
                self.b_carry_comb = self.b_carry_by_2
                self.b_sum_comb = self.b_sum_by_2
            elif self.shift_b_2_odd:
                self.b_carry_comb = self.a_minus_b_by_2_carry
                self.b_sum_comb = self.a_minus_b_by_2_sum
            elif ~unsigned(~self.delta[self.delta_msb]) & self.ab_after_lsb_2:
                if self.shift_b_8_odd & self.ab_after_lsb_3:
                    self.b_carry_comb = self.a_b_carry_by_8
                    self.b_sum_comb = self.a_b_sum_by_8
                else:
                    self.b_carry_comb = self.a_delta_update_add_carry
                    self.b_sum_comb = self.a_delta_update_add_sum
            elif ~unsigned(~self.delta[self.delta_msb]):
                if self.shift_b_8_odd & self.a_minus_b_after_lsb_3:
                    self.b_carry_comb = self.a_delta_update_sub_first_carry_by_2
                    self.b_sum_comb = self.a_delta_update_sub_first_sum_by_2
                else:
                    self.b_carry_comb = self.a_delta_update_sub_first_carry
                    self.b_sum_comb = self.a_delta_update_sub_first_sum
            else:
                self.b_carry_comb = self.b_carry
                self.b_sum_comb = self.b_sum
        else:
            self.b_carry_comb = self.b_carry
            self.b_sum_comb = self.b_sum


if __name__ == "__main__":
    dut = Update_a_b(bit_length=1024,
                     inter_bit_length=1028,
                     delta_msb=False)

    verilog(dut, filename="Update_a_b.v")

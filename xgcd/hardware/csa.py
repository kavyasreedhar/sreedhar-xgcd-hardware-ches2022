import os
import kratos
from kratos import *

from xgcd.hardware.extended_gcd.half_adder import HalfAdder


class CSAArithRightShift(Generator):
    def __init__(self,
                 bit_length,
                 default_prior_work=False):
        super().__init__("CSAArithRightShift")

        self.bit_length = bit_length
        self.default_prior_work = default_prior_work

        self.final_out_carry = self.input("final_out_carry", self.bit_length)
        self.final_out_sum = self.input("final_out_sum", self.bit_length)

        self.shifted_out_carry = self.output("shifted_out_carry", self.bit_length)
        self.shifted_out_sum = self.output("shifted_out_sum", self.bit_length)

        self.wire(self.shifted_out_sum[self.bit_length - 3, 0], self.final_out_sum[self.bit_length - 2, 1])
        self.wire(self.shifted_out_carry[self.bit_length - 3, 0], self.final_out_carry[self.bit_length - 2, 1])
        
        self.xcn = self.var("xcn", 1)
        self.wire(self.xcn, self.final_out_carry[self.bit_length - 1])
        self.xcn_1 = self.var("xcn_1", 1)
        self.wire(self.xcn_1, self.final_out_carry[self.bit_length - 2])
        self.xsn = self.var("xsn", 1)
        self.wire(self.xsn, self.final_out_sum[self.bit_length - 1])

        if self.default_prior_work:
            self.xsn_1 = self.var("xsn_1", 1)
            self.wire(self.xsn_1, self.final_out_sum[self.bit_length - 2])

            self.wire(self.shifted_out_carry[self.bit_length - 1], self.xcn & self.xsn_1 | ~self.xsn & self.xcn | ~self.xsn & self.xsn_1)
            self.wire(self.shifted_out_sum[self.bit_length - 1], self.xsn)
            self.wire(self.shifted_out_carry[self.bit_length - 2], self.xcn)
            self.wire(self.shifted_out_sum[self.bit_length - 2], self.xsn)

        else:
            self.wire(self.shifted_out_carry[self.bit_length - 1], self.xcn_1 | (self.xcn ^ self.xsn))
            self.wire(self.shifted_out_sum[self.bit_length - 1], self.xcn & self.xsn)
            self.wire(self.shifted_out_carry[self.bit_length - 2], self.xcn & self.xsn)
            self.wire(self.shifted_out_sum[self.bit_length - 2], self.xcn | self.xsn)

class CSAArithRightShift_4(Generator):
    def __init__(self,
                 bit_length,
                 chain_two_shifts=False):
        super().__init__("CSAArithRightShift_4")

        self.bit_length = bit_length
        self.chain_two_shifts = chain_two_shifts

        self.final_out_carry = self.input("final_out_carry", self.bit_length)
        self.final_out_sum = self.input("final_out_sum", self.bit_length)

        self.shifted_out_carry = self.output("shifted_out_carry", self.bit_length)
        self.shifted_out_sum = self.output("shifted_out_sum", self.bit_length)

        if self.chain_two_shifts:
            self.shifted_out_carry_ = self.var("shifted_out_carry_", self.bit_length)
            self.shifted_out_sum_ = self.var("shifted_out_sum_", self.bit_length)

            shift1 = CSAArithRightShift(self.bit_length)
            self.add_child("shift1",
                        shift1,
                        final_out_carry=self.final_out_carry,
                        final_out_sum=self.final_out_sum,
                        shifted_out_sum=self.shifted_out_sum_,
                        shifted_out_carry=self.shifted_out_carry_)

            shift2 = CSAArithRightShift(self.bit_length)
            self.add_child("shift2",
                        shift2,
                        final_out_carry=self.shifted_out_carry_,
                        final_out_sum=self.shifted_out_sum_,
                        shifted_out_sum=self.shifted_out_sum,
                        shifted_out_carry=self.shifted_out_carry)

        else:
            self.xcn = self.var("xcn", 1)
            self.wire(self.xcn, self.final_out_carry[self.bit_length - 1])
            self.xcn_1 = self.var("xcn_1", 1)
            self.wire(self.xcn_1, self.final_out_carry[self.bit_length - 2])
            self.xsn = self.var("xsn", 1)
            self.wire(self.xsn, self.final_out_sum[self.bit_length - 1])

            self.wire(self.shifted_out_sum[self.bit_length - 4, 0], self.final_out_sum[self.bit_length - 2, 2])
            self.wire(self.shifted_out_carry[self.bit_length - 4, 0], self.final_out_carry[self.bit_length - 2, 2])

            self.wire(self.shifted_out_carry[self.bit_length - 1], self.xcn | self.xsn | self.xcn_1)
            self.wire(self.shifted_out_sum[self.bit_length - 1], self.xcn & self.xcn_1 & self.xsn)
            self.wire(self.shifted_out_carry[self.bit_length - 2], self.xcn & self.xcn_1 & self.xsn)
            self.wire(self.shifted_out_sum[self.bit_length - 2], self.xcn | self.xsn | self.xcn_1)

            self.wire(self.shifted_out_carry[self.bit_length - 3], self.xcn & self.xsn)
            self.wire(self.shifted_out_sum[self.bit_length - 3], self.xcn | self.xsn)

class CSAArithRightShift_8(Generator):
    def __init__(self,
                 bit_length,
                 debug_print=False):
        super().__init__("CSAArithRightShift_8")

        self.bit_length = bit_length
        self.debug_print = debug_print

        self.final_out_carry = self.input("final_out_carry", self.bit_length)
        self.final_out_sum = self.input("final_out_sum", self.bit_length)

        self.shifted_out_carry = self.var("shifted_out_carry", self.bit_length)
        self.shifted_out_sum = self.var("shifted_out_sum", self.bit_length)

        self.shifted_out_carry_out = self.output("shifted_out_carry_out", self.bit_length)
        self.shifted_out_sum_out = self.output("shifted_out_sum_out", self.bit_length)
        
        self.xcn = self.var("xcn", 1)
        self.wire(self.xcn, self.final_out_carry[self.bit_length - 1])
        self.xcn_1 = self.var("xcn_1", 1)
        self.wire(self.xcn_1, self.final_out_carry[self.bit_length - 2])
        self.xsn = self.var("xsn", 1)
        self.wire(self.xsn, self.final_out_sum[self.bit_length - 1])

        self.wire(self.shifted_out_sum[self.bit_length - 4, 0], self.final_out_sum[self.bit_length - 2, 2])
        self.wire(self.shifted_out_carry[self.bit_length - 4, 0], self.final_out_carry[self.bit_length - 2, 2])

        self.wire(self.shifted_out_carry[self.bit_length - 1], self.xcn | self.xsn | self.xcn_1)
        self.wire(self.shifted_out_sum[self.bit_length - 1], self.xcn & self.xcn_1 & self.xsn)
        self.wire(self.shifted_out_carry[self.bit_length - 2], self.shifted_out_sum[self.bit_length - 1])
        self.wire(self.shifted_out_sum[self.bit_length - 2], self.shifted_out_carry[self.bit_length - 1])

        self.wire(self.shifted_out_carry[self.bit_length - 3], self.xcn & self.xsn)
        self.wire(self.shifted_out_sum[self.bit_length - 3], self.xcn | self.xsn)

        self.wire(self.shifted_out_carry_out[self.bit_length - 1], self.shifted_out_carry[self.bit_length - 1])
        self.wire(self.shifted_out_sum_out[self.bit_length - 1], self.shifted_out_sum[self.bit_length - 1])
        self.wire(self.shifted_out_carry_out[self.bit_length - 2], self.shifted_out_sum[self.bit_length - 1])
        self.wire(self.shifted_out_sum_out[self.bit_length - 2], self.shifted_out_carry[self.bit_length - 1])

        self.wire(self.shifted_out_sum_out[self.bit_length - 3, 0], self.shifted_out_sum[self.bit_length - 2, 1])
        self.wire(self.shifted_out_carry_out[self.bit_length - 3, 0], self.shifted_out_carry[self.bit_length - 2, 1])

        if self.debug_print:
            self.debug_shifted_out_carry = self.var("debug_shifted_out_carry", self.bit_length)
            self.debug_shifted_out_sum = self.var("debug_shifted_out_sum", self.bit_length)
            self.debug_shifted_out_carry_ = self.var("debug_shifted_out_carry_", self.bit_length)
            self.debug_shifted_out_sum_ = self.var("debug_shifted_out_sum_", self.bit_length)

            self.debug_shifted_out_carry_out = self.output("debug_shifted_out_carry_out", self.bit_length)
            self.debug_shifted_out_sum_out = self.output("debug_shifted_out_sum_out", self.bit_length)
            
            shift1 = CSAArithRightShift(self.bit_length)
            self.add_child("shift1",
                        shift1,
                        final_out_carry=self.final_out_carry,
                        final_out_sum=self.final_out_sum,
                        shifted_out_sum=self.debug_shifted_out_sum,
                        shifted_out_carry=self.debug_shifted_out_carry)
            
            shift2 = CSAArithRightShift(self.bit_length)
            self.add_child("shift2",
                        shift2,
                        final_out_carry=self.debug_shifted_out_carry,
                        final_out_sum=self.debug_shifted_out_sum,
                        shifted_out_sum=self.debug_shifted_out_sum_,
                        shifted_out_carry=self.debug_shifted_out_carry_)

            right_shift = CSAArithRightShift(self.bit_length)
            self.add_child("right_shift",
                        right_shift,
                        final_out_carry=self.debug_shifted_out_carry_,
                        final_out_sum=self.debug_shifted_out_sum_,
                        shifted_out_sum=self.debug_shifted_out_sum_out,
                        shifted_out_carry=self.debug_shifted_out_carry_out)
        
            self.original = self.var("original", self.bit_length)
            self.first = self.var("first", self.bit_length)
            self.second = self.var("second", self.bit_length)
            self.third = self.var("third", self.bit_length)

            self.wire(self.original, self.final_out_carry + self.final_out_sum)
            self.wire(self.first, self.debug_shifted_out_sum + self.debug_shifted_out_carry)
            self.wire(self.second, self.debug_shifted_out_sum_ + self.debug_shifted_out_carry_)
            self.wire(self.third, self.debug_shifted_out_sum_out + self.debug_shifted_out_carry_out)

class DW01_csa(Generator):
    def __init__(self,
                 bit_length=800,
                 DW=True,
                 use_external=True):
        super().__init__(f"{('DW01_csa' if DW else 'CW_csa') if use_external else 'CSA'}")

        self.bit_length = bit_length
        self.DW = DW
        self.use_external = use_external

        if self.DW:
            self.external = True
        
            self.width = self.param("width", clog2(self.bit_length) + 1)

            self.a = self.input("a", self.width)
            self.b = self.input("b", self.width)
            self.c = self.input("c", self.width)
            self.ci = self.input("ci", 1)

            self.carry = self.output("carry", self.width)
            self.sum = self.output("sum", self.width)
            self.co = self.output("co", 1)

        else:
            self.width_ = bit_length
            
            self.width = self.param("width", clog2(self.bit_length) + 1)

            self.a = self.input("a", self.width_)
            self.b = self.input("b", self.width_)
            self.c = self.input("c", self.width_)
            self.ci = self.input("ci", 1)

            self.carry = self.output("carry", self.width_)
            self.sum = self.output("sum", self.width_)
            self.co = self.output("co", 1)

            self.wire(self.carry[0], self.ci)
            self.wire(self.carry[1], (self.a[0] & self.b[0]) | (self.b[0] & self.c[0]) | (self.c[0] & self.a[0]))
            self.wire(self.sum[0], self.a[0] ^ self.b[0] ^ self.c[0])
            self.wire(self.sum[self.width_ - 1], self.a[self.width_ - 1] ^ self.b[self.width_ - 1] ^ self.c[self.width_ - 1])
            self.wire(self.co, (self.a[self.width_ - 1] & self.b[self.width_ - 1]) | (self.b[self.width_ - 1] & self.c[self.width_ - 1]) | (self.c[self.width_ - 1] & self.a[self.width_ - 1]))

            for i in range(1, self.width_ - 1):
                self.wire(self.carry[i + 1], (self.a[i] & self.b[i]) | (self.b[i] & self.c[i]) | (self.c[i] & self.a[i]))
                self.wire(self.sum[i], self.a[i] ^ self.b[i] ^ self.c[i])

class DW01_csa_4(Generator):
    def __init__(self,
                 bit_length=804,
                 is_add=True,
                 DW=True,
                 debug_print=False,
                 check_expect=False):
        super().__init__("DW01_csa_4")

        self.bit_length = bit_length
        self.is_add = is_add
        self.DW = DW
        self.debug_print = debug_print
        self.check_expect = check_expect

        if self.check_expect:
            self.clk = self.clock("clk")
            self.rst_n = self.reset("rst_n", 1)

        self.a_carry = self.input("a_carry", self.bit_length)
        self.a_sum = self.input("a_sum", self.bit_length)
        self.b_carry = self.input("b_carry", self.bit_length)
        self.b_sum = self.input("b_sum", self.bit_length)

        self.final_out_carry = self.output("final_out_carry", self.bit_length)
        self.final_out_sum = self.output("final_out_sum", self.bit_length)
        self.co = self.output("co", 1)

        self.out_carry = self.var("out_carry", self.bit_length)
        self.out_sum = self.var("out_sum", self.bit_length)

        if self.check_expect:
            self.testing_out = self.output("testing_out", self.bit_length)
            self.wire(self.testing_out, self.final_out_carry + self.final_out_sum)

        self.ci = self.var("ci", 1)
        self.b1 = self.var("b1", self.bit_length)
        self.c2 = self.var("c2", self.bit_length)

        if self.is_add:
            self.wire(self.ci, const(0, 1))
            self.wire(self.b1, self.b_carry)
            self.wire(self.c2, self.b_sum)
        else:
            self.wire(self.ci, const(1, 1))
            self.wire(self.b1, ~self.b_carry)
            self.wire(self.c2, ~self.b_sum)

        csa1 = DW01_csa(self.bit_length, DW=self.DW)
        csa1.width.value = self.bit_length
        self.add_child("csa1", csa1,
                    a=self.a_carry,
                    b=self.b1,
                    c=self.a_sum,
                    ci=self.ci,
                    carry=self.out_carry,
                    sum=self.out_sum)
        
        csa2 = DW01_csa(self.bit_length, DW=self.DW)
        csa2.width.value = self.bit_length
        self.add_child("csa2", csa2,
                    a=self.out_sum,
                    b=self.out_carry,
                    c=self.c2,
                    ci=self.ci,
                    carry=self.final_out_carry,
                    sum=self.final_out_sum,
                    co=self.co)

class DW01_csa_shift_only(Generator):
    def __init__(self,
                 bit_length=804,
                 support_signed=True,
                 debug_print=False,
                 check_expect=False):
        super().__init__("DW01_csa_shift_only")

        self.bit_length = bit_length
        self.support_signed = support_signed
        self.debug_print = debug_print
        self.check_expect = check_expect

        self.final_out_carry = self.input("final_out_carry", self.bit_length)
        self.final_out_sum = self.input("final_out_sum", self.bit_length)

        self.shifted_out_carry = self.output("shifted_out_carry", self.bit_length)
        self.shifted_out_sum = self.output("shifted_out_sum", self.bit_length)

        self.shifted_out_carry_inter = self.var("shifted_out_carry_inter", self.bit_length)
        self.shifted_out_sum_inter = self.var("shifted_out_sum_inter", self.bit_length)

        if self.check_expect:
            self.clk = self.clock("clk")
            self.rst_n = self.reset("rst_n", 1)

            self.testing_out = self.var("testing_out", self.bit_length)
            self.wire(self.testing_out, self.shifted_out_carry + self.shifted_out_sum)

            self.testing_expect = self.output("testing_expect", self.bit_length)
            self.wire(self.testing_expect, self.testing_out)

            self.helper = self.var("helper", self.bit_length)
            self.wire(self.helper, self.final_out_carry + self.final_out_sum)
            self.helper_by_2 = self.var("helper_by_2", self.bit_length)
            self.wire(self.helper_by_2, concat(self.helper[self.bit_length - 1], self.helper[self.bit_length - 1, 1]))

            self.is_correct = self.output("is_correct", 1)
            self.wire(self.is_correct, self.testing_out == self.helper_by_2)

        if self.support_signed:
            right_shift = CSAArithRightShift(self.bit_length)
            self.add_child("right_shift",
                        right_shift,
                        final_out_carry=self.final_out_carry,
                        final_out_sum=self.final_out_sum,
                        shifted_out_sum=self.shifted_out_sum_inter,
                        shifted_out_carry=self.shifted_out_carry_inter)
        else:
            self.wire(self.shifted_out_sum_inter, self.final_out_sum >> 1)
            self.wire(self.shifted_out_carry_inter, self.final_out_carry >> 1)

        correct1 = HalfAdder(self.bit_length)
        self.add_child("correct1",
                       correct1,
                       a=self.shifted_out_carry_inter,
                       b=self.shifted_out_sum_inter,
                       cin=(self.final_out_carry[0] & self.final_out_sum[0]),
                       sum=self.shifted_out_sum,
                       carry=self.shifted_out_carry)

class DW01_csa_shift_only_4(Generator):
    def __init__(self,
                 bit_length=804,
                 support_signed=True,
                 debug_print=False):
        super().__init__("DW01_csa_shift_only_4")

        self.bit_length = bit_length
        self.support_signed = support_signed
        self.debug_print = debug_print

        self.final_out_carry = self.input("final_out_carry", self.bit_length)
        self.final_out_sum = self.input("final_out_sum", self.bit_length)

        self.shifted_out_carry = self.output("shifted_out_carry", self.bit_length)
        self.shifted_out_sum = self.output("shifted_out_sum", self.bit_length)

        self.shifted_out_carry_inter = self.var("shifted_out_carry_inter", self.bit_length)
        self.shifted_out_sum_inter = self.var("shifted_out_sum_inter", self.bit_length)
        
        if self.support_signed:
            shift1 = CSAArithRightShift_4(self.bit_length)
            self.add_child("shift1",
                        shift1,
                        final_out_carry=self.final_out_carry,
                        final_out_sum=self.final_out_sum,
                        shifted_out_sum=self.shifted_out_sum_inter,
                        shifted_out_carry=self.shifted_out_carry_inter)
        else:
            self.wire(self.shifted_out_sum_inter, self.final_out_sum >> 2)
            self.wire(self.shifted_out_carry_inter, self.final_out_carry >> 2)
        
        correct1 = HalfAdder(self.bit_length)
        self.add_child("correct1",
                       correct1,
                       a=self.shifted_out_carry_inter,
                       b=self.shifted_out_sum_inter,
                       # we know the lsbs of carry and sum are equal because this number is divisble by 2
                       # this number is divisble by 4 and needs to be corrected for if the numbers are
                       # 1 1, 0 1 or 1 0, 1 0 in the lsbs so we just check the OR of the 2nd to last bits
                       # correction needs to happen in all cases but when both carry and sum are 00 
                       # (i.e., all cases but when both carry and sum are 00 will generate a carry in for
                       # the 3rd LSB)
                       cin=(self.final_out_carry[1] | self.final_out_sum[1]),
                       sum=self.shifted_out_sum,
                       carry=self.shifted_out_carry)

class DW01_csa_shift_only_8(Generator):
    def __init__(self,
                 bit_length=804,
                 support_signed=True,
                 check_expect=False,
                 debug_print=False):
        super().__init__("DW01_csa_shift_only_8")

        self.bit_length = bit_length
        self.support_signed = support_signed
        self.check_expect = check_expect
        self.debug_print = debug_print

        self.final_out_carry = self.input("final_out_carry", self.bit_length)
        self.final_out_sum = self.input("final_out_sum", self.bit_length)

        self.shifted_out_carry = self.output("shifted_out_carry", self.bit_length)
        self.shifted_out_sum = self.output("shifted_out_sum", self.bit_length)

        self.shifted_out_carry_inter = self.var("shifted_out_carry_inter", self.bit_length)
        self.shifted_out_sum_inter = self.var("shifted_out_sum_inter", self.bit_length)

        if self.check_expect:
            self.clk = self.clock("clk")
            self.rst_n = self.reset("rst_n", 1)

        if False: # self.debug_print:
            self.testing_expect = self.output("testing_expect", self.bit_length)
            self.wire(self.testing_expect, self.shifted_out_carry + self.shifted_out_sum)

            self.input_sum = self.var("input_sum", self.bit_length)
            self.wire(self.input_sum, self.final_out_carry + self.final_out_sum)

            self.shifted_out_carry_other = self.output("shifted_out_carry_other", self.bit_length)
            self.shifted_out_sum_other = self.output("shifted_out_sum_other", self.bit_length)

            self.testing_expect_other = self.output("testing_expect_other", self.bit_length)
            self.wire(self.testing_expect_other, self.shifted_out_carry_other + self.shifted_out_sum_other)

            self.equal = self.output("equal", 1)

            # carry propagate add divide by 8 -- for testing purposes
            self.wire(self.shifted_out_carry_other, concat(self.input_sum[self.bit_length - 1], self.input_sum[self.bit_length - 1], self.input_sum[self.bit_length - 1], self.input_sum[self.bit_length - 1, 3]))
            self.wire(self.shifted_out_sum_other, 0)

            self.wire(self.equal, (self.shifted_out_carry_other + self.shifted_out_sum_other == self.shifted_out_sum + self.shifted_out_carry))
            
            self.div = self.output("div", 1)
            self.wire(self.div, ((self.final_out_carry + self.final_out_sum) % 8 == 0))

            self.shifted_out_inter_out = self.var("shifted_out_inter_out", self.bit_length)
            self.wire(self.shifted_out_inter_out, self.shifted_out_carry_inter + self.shifted_out_sum_inter)
        
        if self.support_signed:
            shift1 = CSAArithRightShift_8(bit_length=self.bit_length,
                                        debug_print=self.debug_print)
            self.add_child("shift1",
                        shift1,
                        final_out_carry=self.final_out_carry,
                        final_out_sum=self.final_out_sum,
                        shifted_out_sum_out=self.shifted_out_sum_inter,
                        shifted_out_carry_out=self.shifted_out_carry_inter)
        else:
            self.wire(self.shifted_out_sum_inter, self.final_out_sum >> 3)
            self.wire(self.shifted_out_carry_inter, self.final_out_carry >> 3)
        
        correct1 = HalfAdder(self.bit_length)
        self.add_child("correct1",
                       correct1,
                       a=self.shifted_out_carry_inter,
                       b=self.shifted_out_sum_inter,
                       # we need to add +1 correction divby8 whenever there is a carry into 
                       # the next bit because that info gets lost when we shift in CSA form 
                       # so all cases but when carry and sum are both all 0’s need +1 and 
                       # this can be detected by OR'ing the 3rd lsb of carry and sum since
                       # if this OR is true but the number is not divisible by 8, this result
                       # will not be used anyway
                       cin=(self.final_out_carry[2] | self.final_out_sum[2]),
                       sum=self.shifted_out_sum,
                       carry=self.shifted_out_carry)


if __name__ == "__main__":
    dut = CSAArithRightShift(bit_length=1024)
    verilog(dut, filename="CSAArithRightShift.v")

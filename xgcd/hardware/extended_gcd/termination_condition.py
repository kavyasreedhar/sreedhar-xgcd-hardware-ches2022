import kratos as k
from kratos import *
import math

from xgcd.hardware.csa import *


class TerminationCondition(Generator):
    def __init__(self,
                 bit_length,
                 inter_bit_length,
                 delta_msb,
                 cycle_count_bit_width,
                 constant_time_support=False,
                 debug_print=False):
        super().__init__(f"TerminationCondition", debug=True)

        self.bit_length = bit_length
        self.inter_bit_length = inter_bit_length
        self.delta_msb = delta_msb
        self.cycle_count_bit_width = cycle_count_bit_width
        self.constant_time_support = constant_time_support
        self.debug_print = debug_print

        self.constant_time_cycles = math.ceil(1.51 * self.bit_length + 1)

        self.clk = self.clock("clk")
        self.rst_n = self.reset("rst_n", 1)

        self.a_carry = self.input("a_carry", self.inter_bit_length)
        self.a_sum = self.input("a_sum", self.inter_bit_length)
        self.b_carry = self.input("b_carry", self.inter_bit_length)
        self.b_sum = self.input("b_sum", self.inter_bit_length)

        if self.constant_time_support:
            # configuration register
            self.constant_time = self.input("constant_time", 1)
            self.total_cycle_count = self.input("total_cycle_count", self.cycle_count_bit_width)

        self.done = self.output("done", 1)

        self.a = self.var("a", self.bit_length)
        self.b = self.var("b", self.bit_length)

        self.add_code(self.get_a_b)

        if self.constant_time_support:
            self.add_code(self.set_done)
        else:
            self.wire(self.done, ((self.a == 0) | (self.b == 0)))

    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def get_a_b(self):
        if ~self.rst_n:
            self.a = 0
            self.b = 0
        else:
            self.a = self.a_carry[self.bit_length - 1, 0] + self.a_sum[self.bit_length - 1, 0]
            self.b = self.b_carry[self.bit_length - 1, 0] + self.b_sum[self.bit_length - 1, 0]
    
    @always_comb
    def set_done(self):
        # constant time execution, check if worst-case (max) number
        # of cycles has been reached
        if self.constant_time:
            self.done = (self.total_cycle_count >= self.constant_time_cycles)
        # non constant time execution, check if a or b is 0
        else:
            self.done = ((self.a == 0) | (self.b == 0))


if __name__ == "__main__":
    bit_length = 1024

    dut = TerminationCondition(bit_length=bit_length,
                               inter_bit_length=bit_length + 4,
                               delta_msb=clog2(bit_length),
                               cycle_count_bit_width=12,
                               constant_time_support=False,
                               debug_print=False)

    verilog(dut, filename=f"TerminationCondition.v")

    dut = TerminationCondition(bit_length=bit_length,
                               inter_bit_length=bit_length + 4,
                               delta_msb=clog2(bit_length),
                               cycle_count_bit_width=12,
                               constant_time_support=True,
                               debug_print=False)

    verilog(dut, filename=f"TerminationCondition_CT.v")

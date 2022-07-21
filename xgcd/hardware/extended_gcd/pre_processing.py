import kratos
from kratos import *


class PreProcessing(Generator):
    def __init__(self,
                 inter_bit_length,
                 bit_length,
                 four_shift_factor=True,
                 eight_shift_factor=True,
                 debug_print=False):
        super().__init__(f"PreProcessing", debug=True)

        self.inter_bit_length = inter_bit_length
        self.bit_length = bit_length
        self.four_shift_factor = four_shift_factor
        self.eight_shift_factor = eight_shift_factor
        self.debug_print = debug_print

        self.clk = self.clock("clk")
        self.rst_n = self.reset("rst_n", 1)

        self.A = self.input("A", self.bit_length)
        self.B = self.input("B", self.bit_length)
        self.start = self.input("start", 1)

        self.og_cycle = self.output("og_cycle", 1)
        self.og_a = self.output("og_a", self.inter_bit_length)
        self.og_b = self.output("og_b", self.inter_bit_length)
        self.og_a2 = self.output("og_a2", self.inter_bit_length)
        self.og_b2 = self.output("og_b2", self.inter_bit_length)
        self.og_a3 = self.output("og_a3", self.inter_bit_length)
        self.og_b3 = self.output("og_b3", self.inter_bit_length)
        self.og_a4 = self.output("og_a4", self.inter_bit_length)
        self.og_b4 = self.output("og_b4", self.inter_bit_length)
        self.og_a5 = self.output("og_a5", self.inter_bit_length)
        self.og_b5 = self.output("og_b5", self.inter_bit_length)
        self.og_a6 = self.output("og_a6", self.inter_bit_length)
        self.og_b6 = self.output("og_b6", self.inter_bit_length)
        self.og_a7 = self.output("og_a7", self.inter_bit_length)
        self.og_b7 = self.output("og_b7", self.inter_bit_length)

        if self.four_shift_factor:
            self.add_code(self.set_og_four_factor)
        else:
            self.wire(self.og_a2, 0)
            self.wire(self.og_b2, 0)
            self.wire(self.og_a3, 0)
            self.wire(self.og_b3, 0)

        if self.eight_shift_factor:
            self.add_code(self.set_og_eight_factor)
        else:
            self.wire(self.og_a4, 0)
            self.wire(self.og_b4, 0)
            self.wire(self.og_a5, 0)
            self.wire(self.og_b5, 0)
            self.wire(self.og_a6, 0)
            self.wire(self.og_b6, 0)
            self.wire(self.og_a7, 0)
            self.wire(self.og_b7, 0)

        self.og_b_div4 = self.output("og_b_div4", 1)
        self.og_b_plus_1 = self.var("og_b_plus_1", 2)
        self.wire(self.og_b_div4, ~self.og_b_plus_1[1] & ~self.og_b_plus_1[0])

        self.og_a_div4 = self.output("og_a_div4", 1)
        self.og_a_minus_1 = self.var("og_a_minus_1", 2)
        self.wire(self.og_a_div4, ~self.og_a_minus_1[1] & ~self.og_a_minus_1[0])

        self.og_a_div4_plus = self.output("og_a_div4_plus", 1)
        self.og_a_plus_1 = self.var("og_a_plus_1", 2)
        self.wire(self.og_a_div4_plus, ~self.og_a_plus_1[1] & ~self.og_a_plus_1[0])

        self.add_code(self.set_og_cycle)
        self.add_code(self.set_ogs)

    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def set_og_cycle(self):
        if ~self.rst_n:
            self.og_cycle = 0
        elif self.start:
            self.og_cycle = 1
        else:
            self.og_cycle = 0

    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def set_ogs(self):
        if ~self.rst_n:
            self.og_b = 0
            self.og_a = 0

        elif self.start:
            self.og_a = self.A.extend(self.inter_bit_length)
            self.og_b = self.B.extend(self.inter_bit_length)

            self.og_b_plus_1 = self.B[1, 0] + 1
            self.og_a_minus_1 = self.A[1, 0] - 1
            self.og_a_plus_1 = self.A[1, 0] + 1

            if ~self.A[0]:
                self.og_a = self.A.extend(self.inter_bit_length) + self.B.extend(self.inter_bit_length)
                self.og_a_minus_1 = self.A[1, 0] + self.B[1, 0] - 1
                self.og_a_plus_1 = self.A[1, 0] + self.B[1, 0] + 1

            elif ~self.B[0]:
                self.og_b = self.A.extend(self.inter_bit_length) + self.B.extend(self.inter_bit_length)
                self.og_b_plus_1 = self.A[1, 0] + self.B[1, 0] + 1

    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def set_og_four_factor(self):
        if ~self.rst_n:
            self.og_b2 = 0
            self.og_a2 = 0
            self.og_b3 = 0
            self.og_a3 = 0

        elif self.og_cycle:
            # multiply by 2 = shift right by 1
            self.og_a2 = concat(self.og_a[self.inter_bit_length - 2, 0], const(0, 1))
            self.og_b2 = concat(self.og_b[self.inter_bit_length - 2, 0], const(0, 1))
            # multiply by 3 = 2 * og + 1 * og = shift and add
            self.og_a3 = self.og_a + concat(self.og_a[self.inter_bit_length - 2, 0], const(0, 1))
            self.og_b3 = self.og_b + concat(self.og_b[self.inter_bit_length - 2, 0], const(0, 1))

    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def set_og_eight_factor(self):
        if ~self.rst_n:
            self.og_b4 = 0
            self.og_a4 = 0
            self.og_b5 = 0
            self.og_a5 = 0
            self.og_b6 = 0
            self.og_a6 = 0
            self.og_b7 = 0
            self.og_a7 = 0

        elif self.og_cycle:
            # multiply by 4 = shift right by 2
            self.og_a4 = concat(self.og_a[self.inter_bit_length - 3, 0], const(0, 2))
            self.og_b4 = concat(self.og_b[self.inter_bit_length - 3, 0], const(0, 2))
            # multiply by 5 = 4 * og + 1 * og = shift and add
            self.og_a5 = self.og_a + concat(self.og_a[self.inter_bit_length - 3, 0], const(0, 2))
            self.og_b5 = self.og_b + concat(self.og_b[self.inter_bit_length - 3, 0], const(0, 2))
            # multiply by 6 = 4 * og + 2 * og = 2 shifts in parallel and add
            self.og_a6 = concat(self.og_a[self.inter_bit_length - 3, 0], const(0, 2)) + concat(self.og_a[self.inter_bit_length - 2, 0], const(0, 1))
            self.og_b6 = concat(self.og_b[self.inter_bit_length - 3, 0], const(0, 2)) + concat(self.og_b[self.inter_bit_length - 2, 0], const(0, 1))
            # not critical path, so no need to add another cycle
            # multiply by 7 = og + 4 * og + 2 * og
            self.og_a7 = self.og_a + concat(self.og_a[self.inter_bit_length - 3, 0], const(0, 2)) + concat(self.og_a[self.inter_bit_length - 2, 0], const(0, 1))
            self.og_b7 = self.og_b + concat(self.og_b[self.inter_bit_length - 3, 0], const(0, 2)) + concat(self.og_b[self.inter_bit_length - 2, 0], const(0, 1))


if __name__ == "__main__":
    bit_length = 1024
    four_shift_factor = True
    eight_shift_factor = True
    debug_print = False

    dut = PreProcessing(inter_bit_length=bit_length + 4,
                        bit_length=bit_length,
                        four_shift_factor=four_shift_factor,
                        eight_shift_factor=eight_shift_factor,
                        debug_print=debug_print)

    verilog(dut, filename="PreProcessing.v")
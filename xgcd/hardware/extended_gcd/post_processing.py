import kratos
from kratos import *

from xgcd.hardware.csa import *


class PostProcessing(Generator):
    def __init__(self,
                 inter_bit_length,
                 bit_length,
                 DW=True,
                 debug_print=False):
        super().__init__(f"PostProcessing", debug=True)

        self.inter_bit_length = inter_bit_length
        self.bit_length = bit_length
        self.DW = DW
        self.debug_print = debug_print

        self.clk = self.clock("clk")
        self.rst_n = self.reset("rst_n", 1)

        self.a_out_carry_preshift = self.input("a_out_carry_preshift", self.inter_bit_length)
        self.a_out_sum_preshift = self.input("a_out_sum_preshift", self.inter_bit_length)

        self.u_carry_in = self.input("u_carry_in", self.inter_bit_length)
        self.u_sum_in = self.input("u_sum_in", self.inter_bit_length)
        self.y_carry_in = self.input("y_carry_in", self.inter_bit_length)
        self.y_sum_in = self.input("y_sum_in", self.inter_bit_length)
        self.n_carry_in = self.input("n_carry_in", self.inter_bit_length)
        self.n_sum_in = self.input("n_sum_in", self.inter_bit_length)
        self.l_carry_in = self.input("l_carry_in", self.inter_bit_length)
        self.l_sum_in = self.input("l_sum_in", self.inter_bit_length)

        self.done_inter = self.input("done_inter", 1)
        self.prev_done_inter = self.var("prev_done_inter", 1)
        self.even_case = self.input("even_case", 2)

        self.ab = self.var("ab", self.bit_length)
        self.wire(self.ab, self.a_out_carry_preshift[self.bit_length - 1, 0] + self.a_out_sum_preshift[self.bit_length - 1, 0])
        self.ab_lsb_bl1 = self.var("ab_lsb_bl1", 1)
        self.wire(self.ab_lsb_bl1, self.ab[self.bit_length - 1])

        self.yu_carry = self.var("yu_carry", self.inter_bit_length)
        self.yu_sum = self.var("yu_sum", self.inter_bit_length)
        self.y_u = self.var("y_u", self.inter_bit_length)
        self.wire(self.y_u, self.yu_carry + self.yu_sum)
        self.neg_y_u = self.var("neg_y_u", self.inter_bit_length)
        self.wire(self.neg_y_u, ~self.yu_carry + ~self.yu_sum + 2)
        
        DW01_csa_4_yu = DW01_csa_4(self.inter_bit_length, True, DW=self.DW)
        self.add_child("DW01_csa_4_yu",
                    DW01_csa_4_yu,
                    a_carry=self.u_carry_in,
                    a_sum=self.u_sum_in,
                    b_carry=self.y_carry_in,
                    b_sum=self.y_sum_in,
                    final_out_carry=self.yu_carry,
                    final_out_sum=self.yu_sum)

        self.nl_carry = self.var("nl_carry", self.inter_bit_length)
        self.nl_sum = self.var("nl_sum", self.inter_bit_length)
        self.n_l = self.var("n_l", self.inter_bit_length)
        self.wire(self.n_l, self.nl_carry + self.nl_sum)
        self.neg_n_l = self.var("neg_n_l", self.inter_bit_length)
        self.wire(self.neg_n_l, ~self.nl_carry + ~self.nl_sum + 2)

        DW01_csa_4_nl = DW01_csa_4(self.inter_bit_length, True, DW=self.DW)
        self.add_child("DW01_csa_4_nl",
                    DW01_csa_4_nl,
                    a_carry=self.n_carry_in,
                    a_sum=self.n_sum_in,
                    b_carry=self.l_carry_in,
                    b_sum=self.l_sum_in,
                    final_out_carry=self.nl_carry,
                    final_out_sum=self.nl_sum)

        self.yunl_carry = self.var("yunl_carry", self.inter_bit_length)
        self.yunl_sum = self.var("yunl_sum", self.inter_bit_length)
        self.yunl = self.var("yunl", self.inter_bit_length)
        self.wire(self.yunl, self.yunl_carry + self.yunl_sum)
        self.neg_yunl = self.var("neg_yunl", self.inter_bit_length)
        self.wire(self.neg_yunl, ~self.yunl_carry + ~self.yunl_sum + 2)

        DW01_csa_4_yunl = DW01_csa_4(self.inter_bit_length, True, DW=self.DW)
        self.add_child("DW01_csa_4_yunl",
                    DW01_csa_4_yunl,
                    a_carry=self.nl_carry,
                    a_sum=self.nl_sum,
                    b_carry=self.yu_carry,
                    b_sum=self.yu_sum,
                    final_out_carry=self.yunl_carry,
                    final_out_sum=self.yunl_sum)

        # Bezout coefficients
        self.bezout_a = self.output("bezout_a", self.inter_bit_length)
        self.bezout_b = self.output("bezout_b", self.inter_bit_length)
        self.done_output = self.output("done_output", 1)

        self.add_code(self.set_bezouts)
        self.add_code(self.set_done_output)
        self.add_code(self.set_prev_done_inter)
    
    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def set_done_output(self):
        if ~self.rst_n:
            self.done_output = 0
        elif ~self.done_inter:
            self.done_output = 0
        else:
            self.done_output = 1
    
    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def set_prev_done_inter(self):
        if ~self.rst_n:
            self.prev_done_inter = 0
        else:
            self.prev_done_inter = self.done_inter

    @always_ff((posedge, "clk"), (negedge, "rst_n"))
    def set_bezouts(self):
        if ~self.rst_n:
            self.bezout_a = 0
            self.bezout_b = 0
        elif ~self.done_inter:
            self.bezout_a = 0
            self.bezout_b = 0
        elif self.done_inter & ~self.prev_done_inter:
            if self.even_case == 2:
                if self.ab_lsb_bl1:
                    self.bezout_a = self.neg_yunl[self.inter_bit_length - 1, 0]
                    self.bezout_b = self.neg_n_l[self.inter_bit_length - 1, 0]
                else:
                    self.bezout_a = self.yunl[self.inter_bit_length - 1, 0]
                    self.bezout_b = self.n_l[self.inter_bit_length - 1, 0]
            elif self.even_case == 1:
                if self.ab_lsb_bl1:
                    self.bezout_a = self.neg_y_u[self.inter_bit_length - 1, 0]
                    self.bezout_b = self.neg_yunl[self.inter_bit_length - 1, 0]
                else:
                    self.bezout_a = self.y_u[self.inter_bit_length - 1, 0]
                    self.bezout_b = self.yunl[self.inter_bit_length - 1, 0]
            else:
                if self.ab_lsb_bl1:
                    self.bezout_a = self.neg_y_u[self.inter_bit_length - 1, 0]
                    self.bezout_b = self.neg_n_l[self.inter_bit_length - 1, 0]
                else:
                    self.bezout_a = self.y_u[self.inter_bit_length - 1, 0]
                    self.bezout_b = self.n_l[self.inter_bit_length - 1, 0]
    
    @always_comb
    def set_By_Dy(self):
        if self.neg_gcd:
            self.By = ~self.B_input + 1
            self.Dy = ~self.A_input + 1
        else:
            self.By = self.B_input
            self.Dy = self.A_input


if __name__ == "__main__":
    bit_length = 1024
    dut = PostProcessing(bit_length + 4, bit_length)
    verilog(dut, filename=f"PostProcessing_{bit_length}.v")

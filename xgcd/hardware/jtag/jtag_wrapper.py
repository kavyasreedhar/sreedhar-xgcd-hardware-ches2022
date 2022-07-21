import kratos as k
from kratos import *


class JtagWrapper(Generator):
    def __init__(self,
                 bit_length,
                 use_external=True):
        super().__init__(f"jtag_wrapper", debug=True)

        self.bit_length = bit_length
        self.inter_bit_length = self.bit_length + 5

        self.clk_in = self.clock("clk_in")
        self.rst_n = self.reset("rst_n", 1)

        self.A = self.output("A", self.bit_length)
        self.B = self.output("B", self.bit_length)
        self.constant_time = self.output("constant_time", 1)
        self.bezout_a = self.input("bezout_a", self.inter_bit_length)
        self.bezout_b = self.input("bezout_b", self.inter_bit_length)
        self.clk_en = self.output("clk_en", 1)
        
        self.done = self.input("done", 1)
        
        self.start = self.output("start", 1)

        self.trst_n = self.input("trst_n", 1)
        self.tck = self.input("tck", 1)
        self.tms = self.input("tms", 1)
        self.tdi = self.input("tdi", 1)
        self.tdo = self.output("tdo", 1)

        if use_external:
            self.external = True

        else:
            self.counter = self.var("counter", clog2(self.bit_length * 2))
            self.index = self.var("index", clog2(self.bit_length))
            self.wire(self.index, self.counter[clog2(self.bit_length) - 1, 0])
            self.out_counter = self.var("out_counter", clog2(self.bit_length * 2))
            self.out_index = self.var("out_index", clog2(self.bit_length))
            self.wire(self.out_index, self.out_counter[clog2(self.bit_length) - 1, 0])

            self.wire(self.start, self.counter == self.bit_length * 2 - 1)
            self.wire(self.clk_en, 1)

            self.add_code(self.set_inputs)
            self.add_code(self.set_outputs)

    @always_ff((posedge, "clk_in"), (negedge, "rst_n"))
    def set_inputs(self):
        if ~self.rst_n:
            self.counter = 0
            self.A = 0
        elif self.counter != self.bit_length * 2 - 1:
            if ~self.counter[clog2(self.bit_length * 2) - 1]:
                self.A[self.index] = self.tdi
                self.counter = self.counter + 1
            else:
                self.B[self.index] = self.tdi
                self.counter = self.counter + 1
    
    @always_ff((posedge, "clk_in"), (negedge, "rst_n"))
    def set_outputs(self):
        if ~self.rst_n:
            self.out_counter = 0
            self.tdo = 0
        elif self.done:
            if ~self.out_counter[clog2(self.inter_bit_length * 2) - 1]:
                self.tdo = self.bezout_a[self.out_index]
                self.out_counter = self.out_counter + 1
            else:
                self.tdo = self.bezout_b[self.out_index]
                self.out_counter = self.out_counter + 1


if __name__ == "__main__":
    jtag_wrapper = JtagWrapper()
    verilog(jtag_wrapper, filename="JtagWrapper.v")
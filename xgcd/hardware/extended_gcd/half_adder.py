import kratos
from kratos import *


class HalfAdder(Generator):
    def __init__(self,
                 bit_length):
        super().__init__("HalfAdder")

        self.bit_length = bit_length

        self.a = self.input("a", self.bit_length)
        self.b = self.input("b", self.bit_length)
        self.cin = self.input("cin", 1)

        self.sum = self.output("sum", self.bit_length)
        self.carry = self.output("carry", self.bit_length)

        self.wire(self.carry[0], self.cin)
        self.wire(self.carry[self.bit_length - 1, 1], self.a[self.bit_length - 2, 0] & self.b[self.bit_length - 2, 0])
        self.wire(self.sum, self.a ^ self.b)

if __name__ == "__main__":
    dut = HalfAdder(bit_length=1024)
    verilog(dut, filename="HalfAdder.v")
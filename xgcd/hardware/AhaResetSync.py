# https://github.com/StanfordAHA/AhaM3SoC/blob/8ab1d96f85c3ec2c9a308e383668f7651e6156b5/hardware/logical/AhaPlatformController/verilog/AhaResetSync.v
import kratos as k
from kratos import *


class AhaResetSync(Generator):
    def __init__(self):
        super().__init__(f"AhaResetSync", debug=True)

        self.external = True
        
        self.CLK = self.clock("CLK")
        self.Dn = self.reset("Dn", 1)
        self.Qn = self.output("Qn", 1)

        self.sync_q = self.var("sync_q", 1)
        self.sync_qq = self.var("sync_qq", 1)

        self.wire(self.Qn, self.sync_qq)

    #     self.add_code(self.sync_reset)
    
    # @always_ff((posedge, "CLK"), (negedge, "Dn"))
    # def sync_reset(self):
    #     if ~self.Dn:
    #         self.sync_q = 0
    #         self.sync_qq = 0
    #     else:
    #         self.sync_q = 1
    #         self.sync_qq = self.sync_q
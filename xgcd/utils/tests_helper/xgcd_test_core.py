import magma as m
from magma import *
import fault
import tempfile
import kratos as k
import math
import os
import sys

from xgcd.hardware.extended_gcd.xgcd_top import XGCDTop
from xgcd.functional_models.xgcd_model import xgcd_model
from xgcd.utils.util import *
import shutil


def xgcd_test_core(bit_length,
                   dw_path,
                   A,
                   B,
                   shift_factor_a,
                   shift_factor_b,
                   shift_factor_b_odd,
                   constant_time,
                   constant_time_support,
                   final_clock_factor=4,
                   start_clock_factor=2,
                   debug_print=False, 
                   odd_inputs_only=False,
                   write_cycles_to_csv=False,
                   # use DW01_csa csa module
                   use_external=True):

    assert shift_factor_a == shift_factor_b, "Even reduction factor must be the same for a and b in the functional model."
    assert constant_time == 0 or constant_time == 1, "constant_time configuration must be 0 or 1."
    
    if constant_time == 1:
        assert constant_time_support, "Must have hardware with constant_time support to enable constant_time configuration"

    dut = XGCDTop(bit_length=bit_length,
                  debug_print=debug_print,
                  final_clock_factor=final_clock_factor,
                  start_clock_factor=start_clock_factor,
                  shift_factor_a=shift_factor_a,
                  shift_factor_b=shift_factor_b, 
                  shift_factor_b_odd=shift_factor_b_odd,
                  constant_time_support=constant_time_support,
                  DW=use_external)

    magma_dut = k.util.to_magma(dut, flatten_array=True)
    tester = fault.Tester(magma_dut, magma_dut.clk)

    tester.circuit.clk_en = 1
    tester.circuit.rst_n = 1
    tester.circuit.clk = 1
    tester.step(2)
    tester.circuit.rst_n = 0

    tester.step(2)
    tester.circuit.rst_n = 1

    tester.circuit.start = 1

    if constant_time_support:
        # configuration
        tester.circuit.constant_time = constant_time
    else:
        tester.circuit.constant_time = 0

    A, B = abs(A), abs(B)

    # ensure gcd is 1 for inputs
    if math.gcd(A, B) != 1:
        gcd = math.gcd(A, B)
        A = A // gcd
        B = B // gcd
    
    # for odd inputs only
    if odd_inputs_only:
        while A % 2 == 0:
            A = A // 2
        while B % 2 == 0:
            B = B // 2

    print_debug(debug_print, "Find XGCD of: ", A, B)

    assert math.gcd(A, B) == 1

    # edge case -- initial add if one number is even overflows
    if (A + B >= 2 ** bit_length and (A % 2 == 0 or B % 2 == 0)):
        return

    tester.circuit.A = A
    tester.circuit.B = B

    # get number of cycles needed for computation
    # from functional model and expected results
    # for bezout coefficients
    print("Using our functional model")
    gcd, s, t, cycles, _, = \
        xgcd_model(a=A, 
                    b=B, 
                    bit_length=bit_length,
                    constant_time=(constant_time == 1),
                    reduction_factor_even=shift_factor_b,
                    reduction_factor_odd=shift_factor_b_odd,
                    debug_print=debug_print)

    print_debug(debug_print, "INPUTS: ", A, B, gcd)

    # - this is conservative, not all will require final_clock_factor * 2 cycles
    # - + 4 for extra cycle spillover due to running termination condition at a 
    # slower clock frequency
    gcd_cycles = cycles + start_clock_factor * 2 + final_clock_factor * 2 + 4

    for i in range(gcd_cycles):
        tester.step(2)
        tester.circuit.start = 0

    print_debug(debug_print, "EXPECTED: ", gcd_cycles, s, t)
    print_debug(debug_print, "Reduction factors: ", shift_factor_a, shift_factor_b, shift_factor_b_odd)

    if write_cycles_to_csv:
        with open("gcd_cycles.csv", "a") as f:
            f.write(f"{shift_factor_a}, {shift_factor_b}, {gcd_cycles}, {A}, {B}\n")

    tester.circuit.done.expect(1)
    tester.circuit.bezout_a.expect(s)
    tester.circuit.bezout_b.expect(t)

    # print_debug(debug_print, "EXPECTED: ", gcd_cycles, s, t)

    with tempfile.TemporaryDirectory() as tempdir:
        flags = ["-Wno-fatal"]
        if debug_print:
            tempdir = "XGCD_debug"
            flags = ["-Wno-fatal", "--trace"]

        if use_external:
            if 'DW_PATH' not in os.environ.keys():
                sys.exit( 'Error: DW_PATH is not set (see README.md)!' )
            shutil.copy(dw_path, tempdir)

        tester.compile_and_run(target="verilator",
                            directory=tempdir,
                            flags=flags)

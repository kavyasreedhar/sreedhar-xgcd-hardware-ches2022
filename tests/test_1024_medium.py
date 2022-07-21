import pytest
import os

from xgcd.utils.tests_helper.xgcd_test_core import xgcd_test_core
from xgcd.utils.tests_helper.generate_random_inputs import generate_random_inputs


# Test Parameters
bit_length = 1024
use_seed = True
# if True, test a small number of tests for basic functionality
# if False, test a larger test suite
num_inputs = 50

numbers = generate_random_inputs(bit_length=bit_length,
                                 use_seed=use_seed,
                                 num_inputs=num_inputs)

dw_path = os.getenv("DW_PATH")

@pytest.mark.parametrize("shift_factor_a, shift_factor_b, shift_factor_b_odd", [(2, 2, 4), (4, 4, 4), (8, 8, 4), (4, 4, 8)])
@pytest.mark.parametrize("constant_time_support, constant_time", [(True, 1), (True, 0), (False, 0)])
@pytest.mark.parametrize("A, B", numbers)
def test_xgcd(A,
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

    xgcd_test_core(bit_length=bit_length,
                   dw_path=dw_path,
                   A=A,
                   B=B,
                   shift_factor_a=shift_factor_a,
                   shift_factor_b=shift_factor_b,
                   shift_factor_b_odd=shift_factor_b_odd,
                   constant_time=constant_time,
                   constant_time_support=constant_time_support,
                   final_clock_factor=final_clock_factor,
                   start_clock_factor=start_clock_factor,
                   debug_print=debug_print,
                   odd_inputs_only=odd_inputs_only,
                   write_cycles_to_csv=write_cycles_to_csv,
                   use_external=use_external)


if __name__ == "__main__":
    # Used to debug specific test cases (without pytest)
    print(f"Test parameters: bit_length {bit_length}, use_seed {use_seed}")
    test_xgcd(A=42398,
              B=10163,
              shift_factor_a=2,
              shift_factor_b=2,
              shift_factor_b_odd=4,
              constant_time=0,
              constant_time_support=False,
              debug_print=True)

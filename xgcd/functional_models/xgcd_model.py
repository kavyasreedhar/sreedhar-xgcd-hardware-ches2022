import argparse
import math
import random
import numpy as np

from xgcd.utils.util import *
from xgcd.functional_models.xgcd_helper import *


def xgcd_model(a,
               b,
               bit_length=1024,
               constant_time=False,
               min_pair_bezout=False,
               reduction_factor_even=4,
               reduction_factor_odd=4,
               debug_print=False):

    og_debug_print = debug_print

    print_debug(debug_print, f"Initial value a: {a}")
    print_debug(debug_print, f"Initial value b: {b}")
    print_debug(debug_print, f"Reduction factor even: {reduction_factor_even}")
    print_debug(debug_print, f"Reduction factor odd: {reduction_factor_odd}")

    # inputs to XGCD
    start_a, start_b = a, b

    # iterations initialization
    iterations = 0
    # for debugging purposes, keep track of the case transitions
    cases = []

    # remove common factors of 2
    # can skip this if gcd known to be 1
    k = 0
    while (a % 2 == 0 and b % 2 == 0):
        k += 1
        a = a // 2
        b = b // 2

    # if one number is even after common factors of 2
    # have been removed, make odd so both inputs to
    # iterations are odd
    even_case = EvenCase.BOTH_ODD
    if a % 2 == 0:
        a = a + b
        even_case = EvenCase.A_EVEN
    elif b % 2 == 0:
        b = a + b
        even_case = EvenCase.B_EVEN

    # initialize Bezout coefficient variables
    u, l, y, n = 1, 0, 0, 1
    delta = 0
    # store the odd inputs to iterations (aka a_m, b_m)
    og_a, og_b = a, b

    if constant_time:
        constant_time_iterations = math.ceil(1.51 * bit_length + 1)

    print_debug(debug_print and even_case != EvenCase.BOTH_ODD, f"Even Case: {even_case}")
    print_debug(debug_print, "Inputs to iterations loop a: ", og_a)
    print_debug(debug_print, "Inputs to iterations loop b: ", og_b)
    
    sample_break_iterations = 1 if constant_time else 4
    break_condition = True
    while break_condition:
        # for sampling termination condition
        for i in range(sample_break_iterations):
    
            print_debug(debug_print, f"a {a} b {b} y {y} n {n} u {u} l {l} delta {delta}")

            iterations += 1

            # a is divisible by 8
            if reduction_factor_even >= 8 and a % 8 == 0:
                a, u, l = update_a_b_even(cases, 8, a, u, l, og_b, og_a, debug_print, 9)
                delta = delta - 3

            # a is divisible by 4 but not by 8
            elif reduction_factor_even >= 4 and a % 4 == 0:
                a, u, l = update_a_b_even(cases, 4, a, u, l, og_b, og_a, debug_print, 1)
                delta = delta - 2

            # a is divisible by 2 but not by 4 or 8
            elif a % 2 == 0:
                a, u, l = update_a_b_even(cases, 2, a, u, l, og_b, og_a, debug_print, 2)
                delta = delta - 1

            # b is divisible by 8
            elif reduction_factor_even >= 8 and b % 8 == 0:
                b, y, n = update_a_b_even(cases, 8, b, y, n, og_b, og_a, debug_print, 10)
                delta = delta + 3

            # b is divisible by 4 but not by 8
            elif reduction_factor_even >= 4 and b % 4 == 0:
                b, y, n = update_a_b_even(cases, 4, b, y, n, og_b, og_a, debug_print, 3)
                delta = delta + 2

            # b is divisible by 2 but not by 4 or 8
            elif reduction_factor_even >= 2 and b % 2 == 0:
                b, y, n = update_a_b_even(cases, 2, b, y, n, og_b, og_a, debug_print, 4)
                delta = delta + 1

            # if a, b are odd, then either a + b or a - b will be divisble by 4

            # a + b is divisible by 4 and delta >= 0 indicates a should be updated
            elif reduction_factor_odd >= 4 and delta >= 0 and (b + a) % 4 == 0:
                a, u, l = update_a_b_odd(cases, 4, a, b, False, u, l, y, n, og_b, og_a, debug_print, 5)
                delta = delta - 1

                # (a + b) was divisible by 8
                if reduction_factor_odd >= 8 and a % 2 == 0:
                    a, u, l = update_a_b_even(cases, 2, a, u, l, og_b, og_a, debug_print, 16)
                    delta = delta - 1

            # a - b is divisible by 4 and delta >= 0 indicates a should be updated
            elif reduction_factor_odd >= 4 and delta >= 0:
                a, u, l = update_a_b_odd(cases, 4, a, b, True, u, l, y, n, og_b, og_a, debug_print, 6)
                delta = delta - 1

                # (a - b) was divisible by 8
                if reduction_factor_odd >= 8 and a % 2 == 0:
                    a, u, l = update_a_b_even(cases, 2, a, u, l, og_b, og_a, debug_print, 18)
                    delta = delta - 1

            # a + b is divisible by 4 and delta < 0 indicates b should be updated
            elif reduction_factor_odd >= 4 and delta < 0 and (b + a) % 4 == 0:
                b, y, n = update_a_b_odd(cases, 4, a, b, False, u, l, y, n, og_b, og_a, debug_print, 7)
                delta = delta + 1

                # (a + b) was divisible by 8
                if reduction_factor_odd >= 8 and b % 2 == 0:
                    b, y, n = update_a_b_even(cases, 2, b, y, n, og_b, og_a, debug_print, 20)
                    delta = delta + 1

            # a - b is divisible by 4 and delta < 0 indicates b should be updated
            # if reduction_factor_odd >= 4, this is the last possible case
            elif reduction_factor_odd >= 4 and delta < 0:
                b, y, n = update_a_b_odd(cases, 4, a, b, True, u, l, y, n, og_b, og_a, debug_print, 8)
                delta = delta + 1

                # (a - b) was divisible by 8
                if reduction_factor_odd >= 8 and b % 2 == 0:
                    b, y, n = update_a_b_even(cases, 2, b, y, n, og_b, og_a, debug_print, 22)
                    delta = delta + 1

            # update with (a - b) / 2 for odd reduction factor of 2
            # update a if delta >= 0
            elif reduction_factor_odd == 2 and delta >= 0:
                a, u, l = update_a_b_odd(cases, 2, a, b, True, u, l, y, n, og_b, og_a, debug_print, 11)
                delta = delta - 1
            
            # update b if delta < 0
            elif reduction_factor_odd == 2 and delta < 0:
                b, y, n = update_a_b_odd(cases, 2, a, b, True, u, l, y, n, og_b, og_a, debug_print, 12)
                delta = delta + 1

        # constant time breaks after maximum (worst-case) number of iterations
        if constant_time:
            break_condition = (iterations < constant_time_iterations)
            # only print updates during the non-zero iterations for ease of debugging
            debug_print = (a != 0 and b != 0) and og_debug_print
        # non constant time breaks when a or b is 0
        else:
            break_condition = (a != 0 and b != 0)
    
    debug_print = og_debug_print
    print_debug(debug_print and constant_time, "Note that constant-time debug only prints while variables change.")

    print_debug(debug_print, f"Before post-processing step y: ", y)
    print_debug(debug_print, f"Before post-processing step n: ", n)
    print_debug(debug_print, f"Before post-processing step u: ", u)
    print_debug(debug_print, f"Before post-processing step l: ", l)
    print_debug(debug_print, f"Before post-processing step u + y: ", u + y)
    print_debug(debug_print, f"Before post-processing step u + y: ", l + n)

    if constant_time:
        print_debug(debug_print, f"Constant-time sanity checks: ")
        print_debug(debug_print, f" Cycles: {iterations}")
        print_debug(debug_print, f" Expected: {constant_time_iterations}")
        print_debug(debug_print, f" Bit Length: {bit_length}")
    
    gcd = a + b
    gcd = gcd * 2**k
    u = u + y
    l = l + n

    if even_case == EvenCase.A_EVEN:
        l = u + l
    elif even_case == EvenCase.B_EVEN:
        u = u + l
        
    print_debug(debug_print, f"Results: u {u} l {l}")
    print_debug(debug_print, f"a {a} b {b} delta {delta} y {y} n {n} u {u} l {l}")

    assert abs(gcd) == math.gcd(start_a, start_b), f"a: {start_a}, b: {start_b}, expected: {math.gcd(start_a, start_b)}, computed: {abs(gcd), a, b}"
    assert u * start_a + l * start_b == gcd, f"a: {start_a}, b: {start_b}, u: {u}, l: {l}, gcd: {gcd}, computed: {u * start_a + l * start_b}"
    
    if min_pair_bezout:
        print_debug(debug_print, "Finding minimum Bezout coefficients...")

        old_u, old_l = u, l
        k = u // (start_b // gcd)

        if k != 0:
            u = u - k * (start_b // gcd)
            l = l + k * (start_a // gcd)

        print_debug(debug_print, f"Min Bezout debug k {k}, u {u}, l {l}, start_b {start_b}, gcd {gcd}, old_u {old_u}, old_l {old_l}")

        # Bezout identity assert
        assert u * start_a + l * start_b == gcd, f"a: {start_a}, b: {start_b}, u: {u}, l: {l}, gcd: {gcd}, computed: {u * start_a + l * start_b}"
        # minimum Bezout coefficients asserts
        assert abs(u) <= abs(start_b / gcd), f"abs u: {abs(u)}, abs start_b / gcd: {abs(start_b / gcd)}"
        assert abs(l) <= abs(start_a / gcd), f"abs l: {abs(l)}, abs start_a / gcd: {abs(start_a / gcd)}"

    if gcd < 0:
        assert -u * start_a + -l * start_b == abs(gcd)
        u = -u
        l = -l

    assert u * start_a + l * start_b == abs(gcd), f"{math.gcd(start_a, start_b)}"

    print_debug(debug_print, f"Returned results: u {u}")
    print_debug(debug_print, f"Returned results: l {l}")
    print_debug(debug_print, f"Returned results: iterations {iterations}")

    return gcd, u, l, iterations, cases

def main_testing(bit_length,
                 num_tests,
                 input_bit_length,
                 is_random=True,
                 test_data=None,
                 print_summary=True,
                 constant_time=False,
                 min_pair_bezout=False,
                 reduction_factor_even=4,
                 reduction_factor_odd=4,
                 debug_print=False):

    if not is_random:
        assert test_data is not None, "Please provide test data if not using randomized inputs."

    max_num = 2**input_bit_length - 1

    total_iterations = 0
    max_iterations = 0

    cases = []
  
    if is_random:
        if num_tests == 1:
            min_num = 1
            tests = [(random.randint(min_num, max_num), random.randint(min_num, max_num))]
        else:
            # min_num_list = [2**(input_bit_length - 1) - 1, 1]
            min_num_list = [2**(input_bit_length - 1) - 1]
            tests = []
            for min_num in min_num_list:
                tests += [(random.randint(min_num, max_num), random.randint(min_num, max_num)) for i in range(num_tests // len(min_num_list))]
    else:
        tests = test_data
    
    num_tests = len(tests)
    num_tests_iterations = 0

    print()
    print(f"Running {num_tests} tests...")

    for i in range(len(tests)):
        if i % 100 == 0:
            print(f"{i} / {num_tests} tests have successfully completed.")

        if is_random:
            (A, B) = tests[i]
        else:
            assert (len(tests[i]) == 2) or len(tests[i] == 3), "Invalid test_data...please format test_data list consisting of tuples with pairs of XGCD inputs (e.g. [(4, 5),...,(6, 7)]"
            if len(tests[i]) == 3:
                (B, A, C) = tests[i]
            elif len(tests[i]) == 2:
                (B, A) = tests[i]

        gcd = math.gcd(A, B)
        if gcd != 1:
            A = A // gcd
            B = B // gcd
        assert math.gcd(A, B) == 1, "GCD for inputs is not 1"

        if A == B and A == 1:
            continue
        
        # for odd inputs only
        # while A % 2 == 0:
        #     A = A // 2
        # while B % 2 == 0:
        #     B = B // 2

        _, _, _, iterations, cases_list = \
            xgcd_model(a=A,
                       b=B, 
                       bit_length=bit_length,
                       debug_print=debug_print, 
                       constant_time=constant_time,
                       min_pair_bezout=min_pair_bezout,
                       reduction_factor_even=reduction_factor_even,
                       reduction_factor_odd=reduction_factor_odd)

        total_iterations += iterations
        if iterations > max_iterations:
            max_iterations = iterations

        # -1 separates XGCD executions (so that we do not include the transition
        # from the end of one iteration to the next in case transition stats
        cases_list.append(-1)
        cases += cases_list

        num_tests_iterations += 1

    if print_summary:
        print()
        print(f"All {num_tests} tests have successfully completed.")

        print()
        print("Summary stats for our algorithm")
        print("-------------------------------")
        print(f"Average number of iterations across the {num_tests} tests: ", total_iterations / num_tests_iterations)
        print(f"Maximum number of iterations across the {num_tests} tests:", max_iterations)
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extended GCD functional model")
    parser.add_argument('--bit_length', type=int, default=1024, help="bit_length for XGCD")
    parser.add_argument('--diff_bit_lengths', default=False, action="store_true", help="XGCD design + input bit_lengths differ (intentionally)")
    parser.add_argument('--input_bit_length', type=int, default=1024, help="bit_length for inputs for XGCD")
    parser.add_argument('--debug', default=False, action="store_true", help="show debug print statements")
    parser.add_argument('--random', default=True, action="store_true", help="use random inputs")
    parser.add_argument('--use_seed', default=True, action="store_true", help="use seed for random inputs")
    parser.add_argument('--num_tests', type=int, default=1024, help="number of random tests to run")
    parser.add_argument('--constant_time', default=False, action="store_true", help="constant-time XGCD (worst-case number of iterations)")
    parser.add_argument('--min_pair_bezout', default=False, action="store_true", help="return minimum Bezout coefficient values in XGCD")
    parser.add_argument('--reduction_factor_even', type=int, default=8, help="Factor of 2 to reduce b by each cycle if even")
    parser.add_argument('--reduction_factor_odd', type=int, default=4, help="Factor of 2 to reduce b when odd by each cycle if even")

    args = parser.parse_args()

    print("Test Stats: ")
    print(args)

    if args.use_seed:
        random.seed(0)

    main_testing(bit_length=args.bit_length,
                 input_bit_length=args.input_bit_length if args.diff_bit_lengths else args.bit_length,
                 num_tests=args.num_tests,
                 is_random=args.random,
                 test_data=[],
                 print_summary=True,
                 constant_time=args.constant_time,
                 min_pair_bezout=args.min_pair_bezout,
                 reduction_factor_even=args.reduction_factor_even,
                 reduction_factor_odd=args.reduction_factor_odd,
                 debug_print=args.debug)

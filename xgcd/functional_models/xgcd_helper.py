import math
from enum import IntEnum

from xgcd.utils.util import print_debug


class EvenCase(IntEnum):
    A_EVEN = 0
    B_EVEN = 1
    BOTH_ODD = 2


# helper functions
def bezout_update(u, l, og_b, og_a, debug_print):
    if u % 2 == 1:
        assert l % 2 == 1
        
        print_debug(debug_print, "in bezout_update ", u, u + og_b, (u + og_b) // 2)
        print_debug(debug_print, "in bezout_update ", l, l - og_a, (l - og_a) // 2)
        
        u = (u + og_b) // 2
        l = (l - og_a) // 2
    else:
        assert l % 2 == 0
        
        u = u // 2
        l = l // 2
    return u, l

def update_a_b_even(cases, power, a, u, l, og_b, og_a, debug_print, case):

    print_debug(debug_print, f"even update_a_b: case {case}")

    a = a // power
    log_power = int(math.log2(power))

    for i in range(log_power):
        u, l = bezout_update(u, l, og_b, og_a, debug_print)  
    
    cases.append(case)
    return a, u, l

def update_a_b_odd(cases, power, a, b, sub, u, l, y, n, og_b, og_a, debug_print, case):

    print_debug(debug_print, f"odd update_a_b: case {case} sub {sub}")

    if sub:
        b, y, n = -b, -y, -n

    print_debug(debug_print, f"odd update_a_b: u, l (negated if sub) {u} {l}")

    a = (b + a) // power
    log_power = int(math.log2(power))

    u, l = y + u, n + l

    print_debug(debug_print, f"odd update_a_b: u, l (after add/sub) {u} {l}", u, l)

    for i in range(log_power):
        u, l = bezout_update(u, l, og_b, og_a, debug_print)
        print_debug(debug_print, f"odd update_a_b: u, l (loop divide by 2) {u} {l}")
    
    cases.append(case)
    return a, u, l

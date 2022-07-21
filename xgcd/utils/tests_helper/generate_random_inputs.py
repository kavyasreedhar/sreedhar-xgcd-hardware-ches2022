
import random


def generate_random_inputs(bit_length, use_seed, num_inputs):

    if use_seed:
        random.seed(0)

    # randomized test data
    max_num_N = 2**(bit_length) - 1
    min_num_N = 2**(bit_length - 1) - 1
    max_num_D = min_num_N
    min_num_D = 1

    if num_inputs == 1:
        return [(random.randint(min_num_N, max_num_N),
                random.randint(min_num_D, max_num_D))]

    numbers = [(random.randint(min_num_N, max_num_N),
                random.randint(min_num_D, max_num_D))
            for _ in range(num_inputs // 2)]

    max_num = 2**(bit_length) - 1
    min_num = 1

    numbers += [(random.randint(min_num, max_num),
                random.randint(min_num, max_num))
                for _ in range(num_inputs // 2)]
    
    return numbers

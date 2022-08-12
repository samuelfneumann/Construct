def test_fn(x):
    import numpy as np
    import time
    newRNG = np.random.default_rng(int(time.time()))
    x.bit_generator.state = newRNG.bit_generator.state


def identity(x):
    return x

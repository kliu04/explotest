import numpy as np

from explotest import explore


@explore
def target():
    return np.sin(np.pi / 2)


target()

import caller
from explotest.explore import explore


@explore
def callee(x, y, z):
    caller.not_under_test()

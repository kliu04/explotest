import callee
from explotest.explore import explore


@explore
def caller():
    callee.callee(1, 2, 3)


def not_under_test():
    pass

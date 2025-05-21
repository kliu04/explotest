import callee
from explotest.explore import explore


@explore
def subroutine():
    callee.function(1, 2, 3)


def not_under_test():
    pass


if __name__ == "__main__":
    subroutine()

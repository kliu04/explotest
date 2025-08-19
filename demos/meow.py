import big_bad_global
from explotest import explore


@explore
def foo():
    print("AA" * 4000)
    big_bad_global.a.append("test1")
    return False


foo()

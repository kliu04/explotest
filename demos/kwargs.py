from explotest.explore import explore


@explore
def contrived_function(a, b=3, *args, c=None, d=2, **kwargs):
    # args is a tuple
    return 1


@explore
def contrived_function2(a, b=3):
    return 2


@explore
def contrived_function3(a, b=3, *args):
    return 2


@explore
def chat_gpt_contrived_function(pos1, pos2, /, p_or_k, *, k1, k2=42, **kwargs):
    pass


if __name__ == "__main__":
    contrived_function(1, 2, c=3)
    contrived_function(1, 2, 3, 4, 5, c=6, d=7, e=8, f=9, g=10)
    contrived_function(1)
    contrived_function2(1)
    contrived_function2(1, 2)
    contrived_function3(1, 2)
    chat_gpt_contrived_function(1, 2, p_or_k=3, k1=4)

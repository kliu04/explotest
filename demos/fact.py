# @explore(mode=Mode.SLICE)


def fact(n):
    def fact(n, rsf):
        if n == 0:
            return rsf
        else:
            return fact(n - 1, rsf * n)

    return fact(n, 1)


print(fact(5))

## SLICE when n == 1

n = 5
rsf = 1

rsf = rsf * 5

n = n - 1  # n = 4?
rsf = rsf * 4

n = n - 1
rsf = rsf * 3

n = n - 1
rsf = rsf * 2

n = n - 1
rsf = rsf * 1

n = n - 1

print(rsf)

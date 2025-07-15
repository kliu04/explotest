w1 = "a"
w2 = "b"


def foo(a, b, c):
    pass


x = 1
x = 2
y = 3
temp_0 = x + y
foo(temp_0, 2, 3)
temp_0 = [1, 2, 3]
foo(*temp_0)

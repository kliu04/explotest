w1 = "a"
w2 = "b"


def foo(a, b, c):
    pass


x = 1
x = 2
y = 3
temp_0 = x + y
temp_1 = 2
temp_2 = 3
foo(temp_0, temp_1, temp_2)
temp_0 = [1, 2, 3]
foo(*temp_0)

def pos_only(a, b, c, d):
    pass


def pos_and_kw(a, b, c=None, d=None):
    pass


def kw_only(a=None, b=None, c=None, d=None):
    pass


def pos_and_kw_with_seps(a, b, /, *, c=None, d=None):
    pass


def all_types(a, b, /, e, f=None, *, c=None, d=None):
    pass


def args_and_kwargs(*args, **kwargs):
    return args[0] + kwargs["foo"]


def all_types(a, b, /, e, *args, f=None, c=None, d=None, **kwargs):
    pass


def foo():
    pass


w, x, y, z = 1, 1, 1, 1
a, b, c, d = w, x, y, z
# pos_only(w, x, y, z)
# pos_and_kw(w, x, y, z)
# pos_and_kw(w, x, d=z, c=y)
# pos_and_kw(w, x, d=z)
# kw_only(a, x, y)
# pos_and_kw_with_seps(w, x, c=c)
# foo()
x = 1
y = 2
z = 3
args_and_kwargs(x, y, z, 4, foo=w, bar=z)

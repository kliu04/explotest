from explotest import explore, Mode


f = open("file.txt")

list_of_obj = ["a"]


@explore(mode=Mode.PICKLE)
def foo(x):
    list_of_obj[0]
    print(x)


foo(f)

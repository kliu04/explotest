from explotest import explore


f = open("file.txt")

list_of_obj = ["a"]


@explore(mode="p")
def foo(x):
    list_of_obj[0]
    print(x)


foo(f)

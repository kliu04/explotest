from typing import Self

from explotest import explore, Mode


class Node:
    next: Self | None
    val: int

    def __init__(self, next, val):
        self.next = next
        self.val = val

    def method(self):
        return 1


@explore(mode=Mode.RECONSTRUCT)
def return_ll(n, acc):
    if n is None:
        return acc
    else:
        return return_ll(n.next, acc + [n])


node = Node(Node(Node(None, 1), 2), 3)
return_ll(node, [])

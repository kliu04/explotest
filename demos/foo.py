from explotest.explore import explore


class Node:
    """Invariant: all values in a tree are unique"""

    def __init__(self, val: int) -> None:
        self.val = val
        self.left: Node | None = None
        self.right: Node | None = None


class BST:
    def __init__(self):
        self.root = None

    @explore
    def _search(self, node: Node | None, value: int) -> Node | None:
        if node is None:
            return None
        if node.val == value:
            return node
        if node.val < value:
            return self._search(node.left, value)
        else:
            return self._search(node.right, value)

    def search(self, value: int) -> Node | None:
        """Search the tree rooted at root for value, returning that node if found, else None"""
        return self._search(self.root, value)

    def _insert(self, node: Node | None, key: int) -> Node:
        if node is None:
            return Node(key)
        if key < node.val:
            node.left = self._insert(node.left, key)
        elif key > node.val:
            node.right = self._insert(node.right, key)
        return node

    def insert(self, key: int):
        self.root = self._insert(self.root, key)

    def _preorder(self, node: Node | None) -> list[int]:
        if node is None:
            return []
        return [node.val] + self._preorder(node.left) + self._preorder(node.right)

    @explore
    def preorder(self) -> list[int]:
        """Return a list of the preorder traversal of the tree rooted at root"""
        return self._preorder(self.root)


@explore
def identity(x):
    return x


if __name__ == "__main__":
    bst = BST()
    bst.insert(500)
    bst.insert(400)
    bst.insert(600)
    bst.insert(450)
    bst.insert(300)
    bst.search(600)
    print(bst.preorder())
    identity(bst)

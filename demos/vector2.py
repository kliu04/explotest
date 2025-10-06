import explotest


class Vector2:
    instances = 0

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        Vector2.instances += 1

    @explotest.explore(mode="p")
    def __add__(self, other: "Vector2"):
        return Vector2(self.x + other.x, self.y + other.y)

    def __abs__(self):
        return (self.x**2 + self.y**2) ** 0.5

    @property
    def normalized(self):
        length = abs(self)
        return Vector2(self.x / length, self.y / length) if length else Vector2(0, 0)

    @classmethod
    def zero(cls):
        return cls(0, 0)

    def __repr__(self):
        return f"Vector2D({self.x}, {self.y})"

    def __eq__(self, other):
        if not isinstance(other, Vector2):
            return False
        return self.x == other.x and self.y == other.y


v1 = Vector2.zero()
v2 = Vector2(2.7, 3.14)

v1 + v2

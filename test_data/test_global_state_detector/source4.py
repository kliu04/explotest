external = "meow :3"


def target():
    l1 = [1, 2, 3]
    l2 = ["x", "y", "z"]

    tuples = [(x, y) for x in l1 for y in l2]

    # cartestian product
    assert tuples == [
        (1, "x"),
        (1, "y"),
        (1, "z"),
        (2, "x"),
        (2, "y"),
        (2, "z"),
        (3, "x"),
        (3, "y"),
        (3, "z"),
    ]

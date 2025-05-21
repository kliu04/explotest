from explotest.explore import explore


class Bar:
    def __init__(self):
        self.x = 0

    @explore
    def bar(self):
        self.x += 1
        return self.x


if __name__ == "__main__":
    bar = Bar()
    print(bar.bar())
    print(bar.bar())
    print(bar.bar())
    print(bar.bar())
    print(bar.bar())

from typing import List

from explotest import explore, explotest_mark


class Solution:
    @explore(mode="p")
    def pacificAtlantic(self, heights: List[List[int]]) -> List[List[int]]:
        ans = []
        for i in range(len(heights)):
            for j in range(len(heights[0])):
                if x := self.search(i, j, heights):
                    ans.append(x)
        return ans

    @explore(mode="p", mark_mode=True)
    def search(self, y, x, heights):
        pacific = False
        atlantic = False
        visited = set()

        if x == 0:
            explotest_mark()

        # @explore(mode="p")
        def search_recur(y, x):
            nonlocal pacific
            nonlocal atlantic
            if pacific and atlantic:
                return
            if (y, x) in visited:
                return
            visited.add((y, x))
            if y == 0 or x == 0:
                pacific = True
            if y == len(heights) - 1 or x == len(heights[0]) - 1:
                atlantic = True

            cur_height = heights[y][x]

            if x > 0 and heights[y][x - 1] <= cur_height:
                search_recur(y, x - 1)
            if x < len(heights[0]) - 1 and heights[y][x + 1] <= cur_height:
                search_recur(y, x + 1)
            if y > 0 and heights[y - 1][x] <= cur_height:
                search_recur(y - 1, x)
            if y < len(heights) - 1 and heights[y + 1][x] <= cur_height:
                search_recur(y + 1, x)

        search_recur(y, x)

        if pacific and atlantic:
            return [y, x]
        else:
            return None


testcase1 = [
    [1, 2, 2, 3, 5],
    [3, 2, 3, 4, 4],
    [2, 4, 5, 3, 1],
    [6, 7, 1, 4, 5],
    [5, 1, 1, 2, 4],
]
testcase2 = [[1]]
testcase3 = [
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    [36, 37, 38, 39, 40, 41, 42, 43, 44, 11],
    [35, 64, 65, 66, 67, 68, 69, 70, 45, 12],
    [34, 63, 84, 85, 86, 87, 88, 71, 46, 13],
    [33, 62, 83, 96, 97, 98, 89, 72, 47, 14],
    [32, 61, 82, 95, 100, 99, 90, 73, 48, 15],
    [31, 60, 81, 94, 93, 92, 91, 74, 49, 16],
    [30, 59, 80, 79, 78, 77, 76, 75, 50, 17],
    [29, 58, 57, 56, 55, 54, 53, 52, 51, 18],
    [28, 27, 26, 25, 24, 23, 22, 21, 20, 19],
]

print(Solution().pacificAtlantic(testcase1))
print(Solution().pacificAtlantic(testcase2))
# print(Solution().pacificAtlantic(testcase3))

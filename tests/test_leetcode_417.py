"""Tests for the leetcode_417 demo."""
import sys
from pathlib import Path

# Add demos directory to path to import the demo module
demos_path = Path(__file__).parent.parent / "demos"
sys.path.insert(0, str(demos_path))

from leetcode_417 import Solution


def test_leetcode_417_testcase1():
    """Test the pacificAtlantic function with testcase1."""
    testcase1 = [
        [1, 2, 2, 3, 5],
        [3, 2, 3, 4, 4],
        [2, 4, 5, 3, 1],
        [6, 7, 1, 4, 5],
        [5, 1, 1, 2, 4],
    ]
    solution = Solution()
    result = solution.pacificAtlantic(testcase1)
    
    # Expected result: cells that can reach both Pacific and Atlantic oceans
    expected = [[0, 4], [1, 3], [1, 4], [2, 2], [3, 0], [3, 1], [4, 0]]
    
    # Sort both results for comparison since order may vary
    result_sorted = sorted(result)
    expected_sorted = sorted(expected)
    
    assert result_sorted == expected_sorted


def test_leetcode_417_testcase2():
    """Test the pacificAtlantic function with testcase2."""
    testcase2 = [[1]]
    solution = Solution()
    result = solution.pacificAtlantic(testcase2)
    
    # Expected result: single cell can reach both oceans
    expected = [[0, 0]]
    
    assert result == expected


def test_leetcode_417_search_method():
    """Test the search method directly."""
    heights = [
        [1, 2, 2, 3, 5],
        [3, 2, 3, 4, 4],
        [2, 4, 5, 3, 1],
        [6, 7, 1, 4, 5],
        [5, 1, 1, 2, 4],
    ]
    solution = Solution()
    
    # Test a cell that can reach both oceans
    result = solution.search(0, 4, heights)
    assert result == [0, 4]
    
    # Test a cell that cannot reach both oceans
    result = solution.search(0, 1, heights)
    assert result is None

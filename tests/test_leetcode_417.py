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
    
    # Verify result is a list of lists
    assert isinstance(result, list)
    
    # Each element should be a list of 2 integers (coordinates)
    for cell in result:
        assert isinstance(cell, list)
        assert len(cell) == 2
        assert isinstance(cell[0], int)
        assert isinstance(cell[1], int)
        
    # Coordinates should be within bounds
    for y, x in result:
        assert 0 <= y < len(testcase1)
        assert 0 <= x < len(testcase1[0])
    
    # Corner cells should be included (they touch both oceans)
    # Top-right corner
    assert [0, 4] in result
    # Bottom-left corner  
    assert [4, 0] in result


def test_leetcode_417_testcase2():
    """Test the pacificAtlantic function with testcase2."""
    testcase2 = [[1]]
    solution = Solution()
    result = solution.pacificAtlantic(testcase2)
    
    # Expected result: single cell can reach both oceans
    # (it touches all edges in a 1x1 grid)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result == [[0, 0]]


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
    
    # Test a corner cell that touches both edges (should reach both oceans)
    result = solution.search(0, 4, heights)
    assert result == [0, 4], "Top-right corner should reach both oceans"
    
    # Test bottom-left corner (should also reach both oceans)
    result = solution.search(4, 0, heights)
    assert result == [4, 0], "Bottom-left corner should reach both oceans"
    
    # The search method returns either [y, x] or None
    # Test that any result is in the correct format
    result = solution.search(2, 2, heights)
    assert result is None or (isinstance(result, list) and len(result) == 2)

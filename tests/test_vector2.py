"""Tests for the vector2 demo."""
import sys
from pathlib import Path

# Add demos directory to path to import the demo module
demos_path = Path(__file__).parent.parent / "demos"
sys.path.insert(0, str(demos_path))

from vector2 import Vector2


def test_vector2_init():
    """Test Vector2 initialization."""
    v = Vector2(3.0, 4.0)
    assert v.x == 3.0
    assert v.y == 4.0


def test_vector2_zero():
    """Test Vector2.zero() class method."""
    v = Vector2.zero()
    assert v.x == 0
    assert v.y == 0


def test_vector2_add():
    """Test Vector2 addition."""
    v1 = Vector2(1.0, 2.0)
    v2 = Vector2(3.0, 4.0)
    result = v1 + v2
    
    assert result.x == 4.0
    assert result.y == 6.0


def test_vector2_add_with_zero():
    """Test Vector2 addition with zero vector."""
    v1 = Vector2.zero()
    v2 = Vector2(2.7, 3.14)
    result = v1 + v2
    
    assert result.x == 2.7
    assert result.y == 3.14


def test_vector2_abs():
    """Test Vector2 absolute value (magnitude)."""
    v = Vector2(3.0, 4.0)
    magnitude = abs(v)
    assert magnitude == 5.0


def test_vector2_abs_zero():
    """Test Vector2 absolute value of zero vector."""
    v = Vector2.zero()
    magnitude = abs(v)
    assert magnitude == 0.0


def test_vector2_normalized():
    """Test Vector2 normalized property."""
    v = Vector2(3.0, 4.0)
    normalized = v.normalized
    
    # Normalized vector should have magnitude 1
    magnitude = abs(normalized)
    assert abs(magnitude - 1.0) < 0.0001
    
    # Direction should be preserved
    assert abs(normalized.x - 0.6) < 0.0001
    assert abs(normalized.y - 0.8) < 0.0001


def test_vector2_normalized_zero():
    """Test Vector2 normalized property with zero vector."""
    v = Vector2.zero()
    normalized = v.normalized
    
    # Normalized zero vector should be zero
    assert normalized.x == 0
    assert normalized.y == 0


def test_vector2_repr():
    """Test Vector2 string representation."""
    v = Vector2(2.7, 3.14)
    assert repr(v) == "Vector2D(2.7, 3.14)"


def test_vector2_eq():
    """Test Vector2 equality comparison."""
    v1 = Vector2(1.0, 2.0)
    v2 = Vector2(1.0, 2.0)
    v3 = Vector2(2.0, 3.0)
    
    assert v1 == v2
    assert not (v1 == v3)


def test_vector2_eq_with_non_vector():
    """Test Vector2 equality comparison with non-Vector2 object."""
    v = Vector2(1.0, 2.0)
    assert not (v == "not a vector")
    assert not (v == 42)
    assert not (v == [1.0, 2.0])


def test_vector2_instances_counter():
    """Test that Vector2 tracks instance count."""
    initial_count = Vector2.instances
    
    v1 = Vector2(1.0, 2.0)
    assert Vector2.instances == initial_count + 1
    
    v2 = Vector2(3.0, 4.0)
    assert Vector2.instances == initial_count + 2

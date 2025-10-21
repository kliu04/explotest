"""Tests for the environment demo."""
import sys
from pathlib import Path

# Add demos directory to path to import the demo module
demos_path = Path(__file__).parent.parent / "demos"
sys.path.insert(0, str(demos_path))

from environment import empty_env, extend_env, lookup_env, combine_env


def test_empty_env():
    """Test that empty_env creates a working empty environment."""
    env = empty_env()
    
    # Empty env should call the fail function
    result = env("x", lambda var: f"unbound:{var}")
    assert result == "unbound:x"


def test_extend_env():
    """Test that extend_env correctly adds bindings to environment."""
    env0 = empty_env()
    env1 = extend_env(env0, "x", 10)
    
    # Looking up "x" should return 10
    result = env1("x", lambda var: None)
    assert result == 10
    
    # Looking up undefined variable should call fail
    result = env1("y", lambda var: f"unbound:{var}")
    assert result == "unbound:y"


def test_extend_env_multiple_bindings():
    """Test extending environment with multiple bindings."""
    env0 = empty_env()
    env1 = extend_env(env0, "x", 10)
    env2 = extend_env(env1, "y", 20)
    
    # Both bindings should be accessible
    assert env2("x", lambda var: None) == 10
    assert env2("y", lambda var: None) == 20


def test_lookup_env():
    """Test lookup_env function."""
    env0 = empty_env()
    env1 = extend_env(env0, "x", 10)
    env2 = extend_env(env1, "y", 20)
    
    # Successful lookups
    assert lookup_env(env2, "x") == 10
    assert lookup_env(env2, "y") == 20
    
    # Failed lookup should raise exception
    try:
        lookup_env(env2, "z")
        assert False, "Expected exception for unbound variable"
    except Exception as e:
        assert "Unbound variable z" in str(e)


def test_combine_env():
    """Test combining two environments."""
    env0 = empty_env()
    env1 = extend_env(env0, "x", 10)
    env2 = extend_env(env1, "y", 20)
    
    env3 = extend_env(env0, "z", 30)
    env4 = extend_env(env3, "g", 40)
    
    # Combine env2 and env4
    env5 = combine_env(env2, env4)
    
    # All variables should be accessible
    assert lookup_env(env5, "x") == 10
    assert lookup_env(env5, "y") == 20
    assert lookup_env(env5, "z") == 30
    assert lookup_env(env5, "g") == 40


def test_combine_env_priority():
    """Test that first environment takes priority in combine_env."""
    env0 = empty_env()
    env1 = extend_env(env0, "x", 10)
    env2 = extend_env(env0, "x", 20)
    
    # Combine env1 and env2, env1 should take priority
    env3 = combine_env(env1, env2)
    assert lookup_env(env3, "x") == 10

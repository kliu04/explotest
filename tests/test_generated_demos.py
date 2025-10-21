"""Tests to validate the structure of auto-generated test files for demos."""
import ast
from pathlib import Path


def parse_test_file(content: str) -> ast.Module:
    """Parse a test file and return its AST."""
    return ast.parse(content)


def count_fixtures(module: ast.Module) -> int:
    """Count the number of pytest fixtures in a module."""
    count = 0
    for node in ast.walk(module):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Attribute):
                    if decorator.attr == "fixture":
                        count += 1
                elif isinstance(decorator, ast.Name):
                    if decorator.id == "fixture":
                        count += 1
    return count


def get_test_function(module: ast.Module) -> ast.FunctionDef | None:
    """Get the main test function from a module."""
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            # Skip fixture functions
            has_fixture_decorator = False
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Attribute) and decorator.attr == "fixture":
                    has_fixture_decorator = True
                elif isinstance(decorator, ast.Name) and decorator.id == "fixture":
                    has_fixture_decorator = True
            if not has_fixture_decorator:
                return node
    return None


def get_act_phase(test_func: ast.FunctionDef) -> ast.Assign | None:
    """Get the act phase (return_value assignment) from a test function."""
    for stmt in test_func.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == "return_value":
                    return stmt
    return None


def test_extend_env_1_structure():
    """Test that test_extend_env_1.py has the correct structure."""
    # Read the generated test file
    with open("/tmp/test_extend_env_1.py", "r") as f:
        content = f.read()
    
    module = parse_test_file(content)
    
    # Should have 4 fixtures: mock_setup (autouse), generate_env, generate_x0, generate_v
    fixture_count = count_fixtures(module)
    assert fixture_count == 4, f"Expected 4 fixtures, got {fixture_count}"
    
    # Get the test function
    test_func = get_test_function(module)
    assert test_func is not None, "No test function found"
    assert test_func.name == "test_extend_env", f"Expected test_extend_env, got {test_func.name}"
    
    # Test function should have 3 parameters (the generate fixtures)
    assert len(test_func.args.args) == 3, f"Expected 3 parameters, got {len(test_func.args.args)}"
    param_names = [arg.arg for arg in test_func.args.args]
    assert param_names == ["generate_env", "generate_x0", "generate_v"]
    
    # Check act phase exists
    act_phase = get_act_phase(test_func)
    assert act_phase is not None, "Act phase (return_value assignment) not found"
    
    # Verify it's calling environment.extend_env
    call = act_phase.value
    assert isinstance(call, ast.Call), "Act phase should be a function call"
    assert isinstance(call.func, ast.Attribute), "Should be calling a module function"
    assert call.func.attr == "extend_env", f"Expected extend_env, got {call.func.attr}"
    
    # Should have 3 arguments
    assert len(call.args) == 3, f"Expected 3 arguments, got {len(call.args)}"


def test_Solution_pacificAtlantic_1_structure():
    """Test that test_Solution_pacificAtlantic_1.py has the correct structure."""
    with open("/tmp/test_Solution_pacificAtlantic_1.py", "r") as f:
        content = f.read()
    
    module = parse_test_file(content)
    
    # Should have 3 fixtures: mock_setup, generate_self, generate_heights
    fixture_count = count_fixtures(module)
    assert fixture_count == 3, f"Expected 3 fixtures, got {fixture_count}"
    
    # Get the test function
    test_func = get_test_function(module)
    assert test_func is not None, "No test function found"
    assert test_func.name == "test_Solution_pacificAtlantic"
    
    # Test function should have 2 parameters
    assert len(test_func.args.args) == 2, f"Expected 2 parameters, got {len(test_func.args.args)}"
    param_names = [arg.arg for arg in test_func.args.args]
    assert param_names == ["generate_self", "generate_heights"]
    
    # Check act phase exists
    act_phase = get_act_phase(test_func)
    assert act_phase is not None, "Act phase not found"
    
    # Verify it's calling leetcode_417.Solution.pacificAtlantic
    call = act_phase.value
    assert isinstance(call, ast.Call), "Act phase should be a function call"
    # It's calling a method on a class
    assert isinstance(call.func, ast.Attribute), "Should be calling a method"
    assert call.func.attr == "pacificAtlantic"


def test_Vector2___add___1_structure():
    """Test that test_Vector2___add___1.py has the correct structure."""
    with open("/tmp/test_Vector2___add___1.py", "r") as f:
        content = f.read()
    
    module = parse_test_file(content)
    
    # Should have 3 fixtures: mock_setup, generate_self, generate_other
    fixture_count = count_fixtures(module)
    assert fixture_count == 3, f"Expected 3 fixtures, got {fixture_count}"
    
    # Get the test function
    test_func = get_test_function(module)
    assert test_func is not None, "No test function found"
    assert test_func.name == "test_Vector2___add__"
    
    # Test function should have 2 parameters
    assert len(test_func.args.args) == 2, f"Expected 2 parameters, got {len(test_func.args.args)}"
    param_names = [arg.arg for arg in test_func.args.args]
    assert param_names == ["generate_self", "generate_other"]
    
    # Check act phase exists
    act_phase = get_act_phase(test_func)
    assert act_phase is not None, "Act phase not found"
    
    # Verify it's calling Vector2.__add__
    call = act_phase.value
    assert isinstance(call, ast.Call), "Act phase should be a function call"
    assert isinstance(call.func, ast.Attribute), "Should be calling a method"
    assert call.func.attr == "__add__"
    
    # Should have 2 arguments (self, other)
    assert len(call.args) == 2, f"Expected 2 arguments, got {len(call.args)}"


def test_empty_env_1_structure():
    """Test that test_empty_env_1.py has the correct structure."""
    with open("/tmp/test_empty_env_1.py", "r") as f:
        content = f.read()
    
    module = parse_test_file(content)
    
    # Should have 1 fixture: mock_setup (autouse)
    fixture_count = count_fixtures(module)
    assert fixture_count == 1, f"Expected 1 fixture, got {fixture_count}"
    
    # Get the test function
    test_func = get_test_function(module)
    assert test_func is not None, "No test function found"
    assert test_func.name == "test_empty_env"
    
    # Test function should have 0 parameters (no fixtures needed)
    assert len(test_func.args.args) == 0, f"Expected 0 parameters, got {len(test_func.args.args)}"
    
    # Check act phase exists
    act_phase = get_act_phase(test_func)
    assert act_phase is not None, "Act phase not found"
    
    # Verify it's calling environment.empty_env
    call = act_phase.value
    assert isinstance(call, ast.Call), "Act phase should be a function call"
    assert isinstance(call.func, ast.Attribute), "Should be calling a module function"
    assert call.func.attr == "empty_env"
    
    # Should have 0 arguments
    assert len(call.args) == 0, f"Expected 0 arguments, got {len(call.args)}"

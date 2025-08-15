import pytest

import global_state_ex_simple


def test_get_elem_at_end():
    return_value = global_state_ex_simple.get_elem_at_end()
    # assert "world" == return_value


# Strategy: Just restore the state directly.
# Problem: How to separate this `restore_state` fixture?
@pytest.fixture(autouse=True)  # decide on scope of fixture
def restore_state():
    global_state_ex_simple.lst = [
        "hello",
        "world",
    ]  # arr strategy, but we could also unpickle

import dill
import pytest
import mock_top_level_packabe

def test_target():
    return_value = mock_top_level_packabe.target()
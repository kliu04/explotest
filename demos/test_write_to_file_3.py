import dill
import pytest
import iomockdemo

@pytest.fixture(autouse=True)
def mock_setup():
    import os
    os.environ['RUNNING_GENERATED_TEST'] = 'true'

@pytest.fixture
def generate_data():
    data = 'meow2'
    return data

def test_write_to_file(generate_data):
    data = generate_data
    return_value = iomockdemo.write_to_file(data)
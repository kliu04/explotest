# ExploTest

ExploTest is a tool that turns exploratory test runs into unit tests by capturing and serializing run-time arguments.
By adding the `@explore` decorator to any function, ExploTest automatically generates unit tests with assertions based
on the previous execution values.
## Installation
```bash
pip install ExploTest
```

### Local Installation

```bash
python3 -m pip install -e <path/to/explotest>
```

## Usage

On any function or method (except for closures), add the `@explore` decorator. When this function (the
function-under-test or FUT) is called at runtime, a
unit test will be generated and saved in same directory as the file of the FUT.

The `@explore` decorator accepts two optional parameters, `mode` and `explicit_record`.

### Configuration

`mode` determines how the run-time arguments are reconstructed in the unit test:

- Setting this to `"p"` or `"pickle"` results in ExploTest "pickling" (a Python specific binary serialization)
  each argument into a file, then loading this file in the unit test. ExploTest uses
  the [dill](https://dill.readthedocs.io/en/latest/) library
  for pickling, which enables support for function arguments among others. However, objects that cannot be pickled (
  e.g., Pandas DataFrames) cannot be saved. This is the default behaviour.
- Setting this to `"a"` results in ExploTest attempting to reconstruct the parameter by creating a new object
  and setting all its fields to the runtime argument.
  For example, when running the code

```python
class Bar:
    x = 1


@explore(mode="a")
def baz(b):
    return


baz(Bar())
```

the unit test

```python
@pytest.fixture
def generate_b():
    clone_b = scratchpad.Bar.__new__(scratchpad.Bar)
    setattr(clone_b, 'x', 1)
    return clone_b


def test_baz(generate_b):
    b = generate_b
    return_value = scratchpad.baz(b)
    assert return_value is None
```

is generated. This will not work for some objects, namely ones that are "more" than just a collection of fields or have
fields that cannot be `setattr`'d. In this case,
ExploTest will try to fall back on pickling.

`explicit_record` determines when ExploTest generates a unit test. By default, this is `False` and so ExploTest
generates a unit test everytime
a function with the `@explore` decorator is called. However, this may become unwieldy if the function is called many
times and
only certain tests are desired. By setting `explicit_record` to `True` in a function, a unit test will only be created
if the function body calls
`explotest_record()`. Note that due to implementation details, this is not thread safe.

For example,

```python
@explore(explicit_record=True)
def fib(n):
    if n <= 1:
        explotest_record()
        return 1
    return fib(n - 1) + fib(n - 2)
```

A unit test will only be generated for when `n <= 1`.

## Development Setup

Create a venv, then install `pip-tools`. Run `pip-compile` as specified.

```bash
python3 -m venv .venv
pip install pip-tools
pip-compile -o requirements.txt ./pyproject.toml
pip install -r requirements.txt
```

## Copyright

ExploTest is free and open source software, licensed under the GNU LGPL v3 or any later version.

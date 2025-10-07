# ExploTest

ExploTest is a tool to create unit tests from exploratory test runs.

This project is currently under active development and API breaks can occur at any time.

## Installation
```bash
pip install ExploTest
```

### Local Installation

```bash
python3 -m pip install -e <path/to/explotest>
```

## Usage
On any function or method (except for closures), add the `@explore` decorator. 

We accept two optional settings, `mode` and `mark_mode`:
- `mode` can be either `"p"` or `"a"` (default is `"p"`) to change the reconstruction mode.
- `mark_mode` can be either `False` or `True` (default is `False`); if set to `True` tests are only generated if execution reaches a `explotest_mark()` function.

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

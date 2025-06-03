# ExploTest

ExploTest is a tool to create unit tests from exploratory test runs.

This project is currently under active development and API breaks can occur at any time.

## Installation (Currently not live!)
```bash
pip install ExploTest
```

### Local Installation

```bash
python3 -m pip install -e .
```

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

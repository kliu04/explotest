# ExploTest

ExploTest is a tool to create unit tests from exploratory test runs.


## Installation
```bash
pip install ExploTest
```

## Setup for development:

Create a venv, then install `pip-tools`. Run `pip-compile` as specified.

```bash
python3 -m venv .venv
pip install pip-tools
pip-compile -o requirements.txt ./pyproject.toml
pip install -r requirements.txt
```

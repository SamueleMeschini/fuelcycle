# Contributing to OpenFC

OpenFC welcomes issues, documentation improvements, tests, and code contributions.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

Before opening a pull request, run:

```bash
make check
make docs
```

Keep changes focused. Changes to the physical model or numerical solver should include a
reproducible validation case and explain the expected scientific impact. Refactors that do
not alter the model should preserve existing equations, parameters, and solver behavior.

## Pull requests

Please describe the motivation, the affected public API, and the checks you ran. New public
classes and functions should include docstrings and tests where practical.

# Contributing

Open an issue before changing public behavior. Explain the problem, the expected result and the versions you tested. Use synthetic slips and credentials in reproductions.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt -e .
ruff check .
ruff format --check .
mypy --strict src
python -m pytest
python -m build
python -m twine check dist/*
```

Add regression tests for behavior changes and update both READMEs when a public option changes. Never include API keys or customer data. Submit changes through a pull request; the checks run on every supported Python version.

Release maintainers merge the automated version pull request, then approve the release environment. Publishing requires the PyPI trusted publisher to be configured for this repository and the publish workflow. No long-lived publishing token is used.

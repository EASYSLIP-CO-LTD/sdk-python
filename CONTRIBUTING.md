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

Release maintainers run CI on the automated version pull request before merging it. `.github/workflows/release.yml` then publishes through the `release` environment in the same run that creates the release. See [the release guide](RELEASING.md) for CI dispatch, approval and existing-tag reruns. No personal access token or GitHub App is required.

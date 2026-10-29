# Tests

## Run all the tests
```bash
tox
```

## Run tests for a specific Python version

```bash
tox -e python3.12-extra-deps
```

## Filtering tests further

```bash
tox -e ... -- path/to/test/file.py -k <substring_of_test_name>
```

To speed up the process, see `tox.ini` and run commands without a tox environment:

```bash
pip install -r test_requirements.txt -r test_requirements_extra.txt

# to run one and only one test
pytest path/to/test/file.py -k <substring_of_test_name>

# to run only flakes
pytest --flakes src/ examples/
```

The Bash commands above are examples of how to run some commands without tox. There are many more possibilities.

## Test cassettes

In some tests, we use the [pytest-recording](https://github.com/kiwicom/pytest-recording) library to record
HTTP requests to local test cassettes to avoid network access in future runs and improve the determinism
of test runs (assuming that the backend will not introduce breaking changes to its contract).

However, pytest-recording supports only HTTP/HTTPS cassettes, so we have a similar mechanism for gRPC requests
[written by us](src/yandex_ai_studio_sdk/_testing/interceptor.py).

It has some limitations. To use it:

1) Add `@pytest.mark.allow_grpc` to the test.

2) Edit `tests/conftest.py:fixture_folder_id` (TODO: make it use environment variables by default)

3) Export authentication credentials to the environment, for example, `export YC_API_KEY="..."` or use another authentication method

4) Run your new test for the first time with `pytest path/to/test/file.py -k <test_name> --generate-grpc`, which will create
  a new cassette file

5) If the test fails or you want to regenerate the cassette, `pytest <...> --regenerate-grpc` will help

6) When you are satisfied with the cassette, run pytest without any `--...-grpc` flags

7) Do not forget to commit the new cassette file.


# Pre-commit hooks

We use https://pre-commit.com/ to improve our PR review experience.

It is generally a good idea to set up pre-commit locally. Otherwise, a bot will process your PR and
will either commit fixes (which you will need to pull or overwrite with a force push)
or fail the checks for issues it cannot fix.


# Documentation

For each PR, we run `sphinx-build -W`, which fails on warnings such as
unresolved references or invalid reStructuredText syntax in docstrings.

To install Sphinx and the other dependencies required for documentation, run

`pip install -r docs/requirements.txt -e .` in the repo root.

To run Sphinx locally to check if there are any errors or warnings,
run `sphinx-build docs docs/_build -E -W` in the repo root.
It generates HTML in the `docs/_build` folder, which you can open if
you want to check how the documentation looks.

You can also install `sphinx-autobuild` and run `sphinx-autobuild docs docs/_build --watch src`
to run a web server (it will be available at http://localhost:8000 by default) and automatically
rebuild the documentation when you save a file.

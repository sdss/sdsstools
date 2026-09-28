# Repository Guidelines

## Project Layout

- Python package code lives in `src/sdsstools/`.
- Tests live in `tests/` and test data lives in `tests/etc/`.
- Package metadata and dependency configuration are in `pyproject.toml`; keep `uv.lock` in sync when dependencies change.
- Do not modify the vendored code under `src/sdsstools/_vendor/` unless the change specifically targets a vendored dependency.

## Development Workflow

- Use the repository virtual environment or `uv` for commands.
- Install the locked development environment with `uv sync`.
- Keep support for Python 3.8 through 3.14 in mind.
- Make focused changes and preserve existing public APIs unless the task requires an intentional change.

## Validation

- Run focused tests first, for example `uv run pytest tests/test_configuration.py`.
- Run the full suite with `uv run pytest`.
- Run linting with `uv run ruff check src/ tests/`.
- Check formatting with `uv run ruff format --check src/ tests/`.
- Add or update tests for behavioral changes. Avoid committing generated coverage output or cache directories.

## Code Style

- Follow the existing Python style and the Ruff configuration in `pyproject.toml`.
- Keep imports sorted and use a maximum line length of 88 characters.
- Prefer small, readable changes over unrelated refactors.

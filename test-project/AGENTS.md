# Repository Guidelines

## Project Structure & Module Organization

- `main.py` contains the FastAPI application, question data, Pydantic request models, and quiz endpoints.
- `static/` contains `index.html`, `style.css`, and `app.js`; FastAPI serves these directly.
- `tests/test_app.py` contains API and static-file tests.
- `docs/issues/` contains feature drafts, including quiz management; drafts are not implemented features.
- `pyproject.toml` defines dependencies and pytest configuration; `uv.lock` records resolved versions.

## Build, Test, and Development Commands

Run commands from this directory with Python 3.13 or newer:

- `uv sync`: synchronize the local environment with project dependencies.
- `uv run uvicorn main:app --reload`: start development at `http://127.0.0.1:8000`.
- `uv sync --group dev`: install testing dependencies.
- `uv run pytest`: run the test suite.

Interactive API documentation is available at `/docs`. No frontend compilation step is required.

## Coding Style & Naming Conventions

Use four-space indentation for Python, snake_case for functions and variables, PascalCase for models, and UPPER_SNAKE_CASE for constants. Follow existing import grouping and add type annotations to new request models.

Use two-space indentation and camelCase identifiers in JavaScript. Preserve Japanese interface text and accessible labels, focus behavior, and error messages. No formatter or linter is currently configured; avoid unrelated formatting changes.

## Testing Guidelines

Tests use pytest and FastAPI's TestClient. Name files `test_*.py` and functions `test_<behavior>`. No numerical coverage threshold is configured.

For API changes, cover valid requests, validation failures, scoring, and the maximum-five-question boundary. Ensure question responses never include correct answers or explanations before submission. For UI changes, manually verify question selection, completion, retry, and mobile layout.

## Commit & Pull Request Guidelines

Git history could not be inspected because of an ownership validation error; no existing commit convention is confirmed. Use concise, imperative commit subjects, such as `Add quiz management validation`.

PR descriptions should explain the resulting behavior, link relevant issues when available, and report test results. Include screenshots for visible interface changes. Update README instructions and the lockfile when dependencies or setup change.

## Architecture & Configuration

Keep scoring and input validation on the server. Choices use zero-based indexes from 0 through 3. Questions currently live in memory; no database or administrator authentication is implemented.

Do not commit secrets, virtual environments, or generated caches.

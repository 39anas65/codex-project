# Repository Guidelines

## Project Structure & Module Organization
The project is currently centered on [`blockchain.py`](/D:/ML-Portfolio/BlockChain/blockchain.py), which contains the `Blockchain` class, Flask app setup, and API routes. Planning and product scope live in [`SPEC.md`](/D:/ML-Portfolio/BlockChain/SPEC.md). Runtime artifacts such as [`error.log`](/D:/ML-Portfolio/BlockChain/error.log) and [`__pycache__/`](/D:/ML-Portfolio/BlockChain/__pycache__) are not source files. As the app grows, keep Flask API logic in `blockchain.py`, place the Streamlit UI in `streamlit_app.py`, and add automated tests under `tests/`.

## Build, Test, and Development Commands
Install and sync dependencies with `uv sync --dev`.

Run the Flask API locally:
```powershell
uv run python blockchain.py
```

Run the Streamlit UI:
```powershell
uv run streamlit run streamlit_app.py
```

Run tests:
```powershell
uv run pytest
```

Useful manual checks:
```powershell
curl http://127.0.0.1:5000/get_chain
curl http://127.0.0.1:5000/is_valid
```

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation. Use `snake_case` for functions, variables, and route helpers; `PascalCase` for classes; and `UPPER_CASE` for constants such as proof-of-work settings. Keep route handlers thin and move reusable logic into class methods or helper functions. Prefer short docstrings on public methods and keep JSON response keys consistent across endpoints.

## Testing Guidelines
Use `pytest` for all new tests. Store them in `tests/` with names like `test_chain_validation.py` or `test_document_verification.py`. Cover core blockchain behavior, API responses, and Streamlit helper logic where practical. Add tests for both success and failure cases, especially validation and verification flows.

## Commit & Pull Request Guidelines
Use short, imperative commit messages such as `Add document verification endpoint` or `Create Streamlit dashboard`. Keep each commit focused on one change. Pull requests should include a brief summary, note any API or UI behavior changes, list test steps, and include screenshots when the Streamlit interface changes.

## Security & Configuration Tips
This repository is educational and stores blockchain data in memory only. Do not commit secrets, tokens, or private keys. Keep SSH keys in your user `.ssh` directory, not in the repository, and avoid committing generated logs or local environment files.

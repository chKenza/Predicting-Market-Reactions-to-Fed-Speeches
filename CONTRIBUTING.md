# Contributing

## 1. Set up the environment

Install [uv](https://docs.astral.sh/uv/) once: `curl -LsSf https://astral.sh/uv/install.sh | sh` (or `brew install uv`).

```bash
uv sync                       # creates .venv with the exact versions in uv.lock
source .venv/bin/activate 
```

In VS Code / Jupyter, select `.venv` as the Python interpreter / kernel.

- After pulling, run `uv sync` again in case dependencies changed.
- Add a package with `uv add <package>`, then commit both `pyproject.toml` and `uv.lock`.
- Dates and paths live in `config.yaml`.

## 2. Add your keys

Add the following in a `.env` file.

- `FRED_API_KEY`: create a free account at [fredaccount.stlouisfed.org](https://fredaccount.stlouisfed.org/apikeys) → **API Keys** → **Request API Key**.
- `HF_TOKEN`: [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) → **Create new token** → type **Read**.

`.env` is git-ignored. Do not commit it.

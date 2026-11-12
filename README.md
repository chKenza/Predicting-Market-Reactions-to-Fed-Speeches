# Predicting-Market-Reactions-to-Fed-Speeches

**FedShock** scores Fed speeches as hawkish or dovish with FOMC-RoBERTa and tests whether that score predicts the 2-year Treasury yield and S&P 500 move on the speech day.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.11–3.12.

```bash
uv sync                    # creates .venv and installs deps from uv.lock
cp .env.example .env       # then add your FRED_API_KEY
```

All dates, the train/test cut-off and file paths are in `config.yaml`. Load them in code with:

```python
from fedshock import load_config, path
cfg = load_config()
path("speeches_raw")
```

## Layout

```
config.yaml          dates, train/test cut-off, paths, model names
pyproject.toml       dependencies (exact versions pinned in uv.lock)
data/raw/            downloaded speeches + market data (git-ignored)
data/processed/      scored sentences, event table (git-ignored)
data/meta/           speakers.csv, excluded_dates.csv (hand-made, versioned)
src/fedshock/        pipeline modules: collect, clean, score, market, features, model, chronos_bench
notebooks/           01_eda … 04_chronos_benchmark
```

## Running a step

```bash
uv run python -m fedshock.collect     # likewise: clean, score, market, features, model, chronos_bench
```

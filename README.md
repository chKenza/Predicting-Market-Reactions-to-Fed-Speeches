# Predicting-Market-Reactions-to-Fed-Speeches

**FedShock** scores Fed speeches as hawkish or dovish with FOMC-RoBERTa and tests whether that score predicts the 2-year Treasury yield and S&P 500 move on the speech day. It builds on *Trillion Dollar Words* (Shah, Paturi, Chava, ACL 2023), which linked its stance score to yield *levels*.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.11–3.12.

```bash
uv sync                    # creates .venv and installs deps from uv.lock
```

All dates, the train/test cut-off and file paths are in `config.yaml`. Load them in code with:

```python
from src import load_config, path
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
src/                 reusable functions: config, collect, clean, score, market, features, model, chronos_bench
analysis/            notebooks that run the analysis (01_eda … 04_chronos_benchmark)
```

## Workflow

`src/` only holds reusable functions; it is not meant to be run directly. The analysis lives in the notebooks in `analysis/`, which import from it:

```python
from src.collect import ...
from src.score import ...
```

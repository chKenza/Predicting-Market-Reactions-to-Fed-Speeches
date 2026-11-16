# FedShock — Predicting Market Reactions to Fed Speeches

**FedShock** scores every Fed speech as hawkish or dovish and tests whether that score predicts how the 2-year Treasury yield and the S&P 500 move on the day of the speech. It builds on *Trillion Dollar Words* (Shah, Paturi, Chava, ACL 2023), which linked its stance score to yield *levels*. FedShock tests whether the score predicts yield *moves* on speech days, using data the paper never saw.

---

---

## 1. Models

| Layer | Model | Role |
| --- | --- | --- |
| Text → score | **FOMC-RoBERTa** (the paper's model) | Labels each sentence hawkish / dovish / neutral, which gives the speech score |
| Text → score (comparison) | Zero-shot open LLM | Same labelling job, by prompting |
| Score → market move | - | Tests and predicts the yield reaction from the score and the controls |
| Price history → market move | **Chronos-2** | Forecasts the next-day yield change from past yields alone, then again with the speech score as a covariate |

---

## 2. Data sources

Speeches come from the BIS archive, topped up from the Fed's own site. The classifier comes from the paper's authors. Market data comes from FRED and Yahoo Finance.

| Data | Source | How to get it | Notes |
| --- | --- | --- | --- |
| Fed speeches, 1996 to mid-2026 (main corpus) | [BIS central bankers' speeches](https://www.bis.org/speeches/central-bank/download) | Per-year ZIPs (1996–2026) or the full ZIP (about 123 MB). In Python: `pip install gingado`, then `from gingado.datasets import load_CB_speeches; load_CB_speeches([2010, 2011, ...])` | Last updated 1 Jul 2026. Keep only Federal Reserve speakers. Some text was converted from PDF, so strip page headers and footers. Non-commercial use only |
| Recent Board speeches (top-up after the BIS cut-off) | [Fed speeches RSS feed](https://www.federalreserve.gov/feeds/speeches.xml) | Scrape each link with `requests` + `BeautifulSoup` | Chair and governors only. The URL holds the speaker and date, e.g. `powell20260531a.htm` |
| Ready-made alternative | [istat-ai/cb-speeches](https://huggingface.co/datasets/istat-ai/cb-speeches) | `load_dataset("istat-ai/cb-speeches")` | BIS speeches 1996 to Sep 2024 with a cleaner institution field. The quickest way to start |
| Hawkish/dovish classifier | [gtfintechlab/FOMC-RoBERTa](https://huggingface.co/gtfintechlab/FOMC-RoBERTa) | `transformers` pipeline, `num_labels=3` | Labels: 0 = dovish, 1 = hawkish, 2 = neutral. CC BY-NC 4.0 |
| Hand-labelled FOMC sentences | [gtfintechlab/fomc-hawkish-dovish](https://github.com/gtfintechlab/fomc-hawkish-dovish) | Clone the repo; data in `training_data/test-and-training` | Train/test splits for 3 seeds. Use it to check the classifier |
| Time-series foundation model | [amazon/chronos-2](https://huggingface.co/amazon/chronos-2) | `pip install "chronos-forecasting>=2.0"`, then `BaseChronosPipeline.from_pretrained("amazon/chronos-2")` and `predict_df(...)` | 120M parameters, runs on CPU or GPU, supports past and known-future covariates. Apache 2.0 |
| 2-year and 10-year Treasury yields | FRED series [DGS2](https://fred.stlouisfed.org/graph?graph_id=484889) and DGS10 | `pip install fredapi` (free API key) or `pandas_datareader.DataReader("DGS2", "fred")` | Daily closing yields in %, updated each business day |
| S&P 500 and volatility | Yahoo Finance: SPY, ^VIX | `pip install yfinance`, then `yf.download(["SPY", "^VIX"], start="2010-01-01")` | Daily prices. Use adjusted close for returns |
| Days to exclude or control for | Fed FOMC calendar; BLS release schedules for CPI and the jobs report | Build a small CSV of dates by hand or by scraping | A speech on a CPI, jobs-report or FOMC day is drowned out by that news |

---

## 3. Workflow

Reusable code goes in `src/`, and the notebooks that run the analysis go in `analysis/`. Train on 2010–2022, test on 2023 onward.

### Step 1 — Setup
- virtual environment and a `requirements.txt`: pandas, numpy, transformers, torch, nltk, yfinance, fredapi, statsmodels, scikit-learn, lightgbm, chronos-forecasting, matplotlib, streamlit.
- Add a `config.yaml` with the date range, the train/test cut-off (`2023-01-01`) and file paths, so nothing is hard-coded.

### Step 2 — Collect the speeches
- Load BIS speeches from 2010 onward and keep Federal Reserve speakers only. Save `date`, `speaker`, `title`, `text` to `data/raw/speeches.parquet`.
- Top up the months after the BIS cut-off from the Fed RSS feed. Remove duplicates on (speaker, date, title).
- Add speaker metadata by hand in `data/meta/speakers.csv`: role (Chair, Vice Chair, governor, regional president) and whether they vote on the FOMC that year.

### Step 3 — Clean and score the text
- Strip headers, footnotes and reference lists, then split into sentences with `nltk.sent_tokenize`.
- Keep policy-relevant sentences with the paper's keyword filter (inflation, interest rate, employment, unemployment, growth, demand, monetary policy, etc.). Drop speeches with fewer than 5 such sentences, which are usually about payments, bank supervision and so on.
- Run `gtfintechlab/FOMC-RoBERTa` on every kept sentence in batches and cache the labels to `data/processed/sentences_scored.parquet`.
- Speech score = (hawkish sentences − dovish sentences) ÷ kept sentences, between −1 and +1.
- Sanity checks:
  - The classifier should reach about 0.7 F1 on the authors' labelled test set.
  - A monthly average of your score should rise in 2022 (hiking cycle) and fall in 2024 (cuts).

### Step 4 — Build the features
- `score`: the speech score from step 3.
- `surprise`: score minus the same speaker's average over their previous 5 speeches. This is the key feature, because markets react to what is new.
- `is_chair`, `is_voter`, `role`, and `n_policy_sentences` as a measure of how much policy content there is.
- Controls known before the speech: VIX the day before and the previous day's 2-year yield change.

### Step 5 — Build the targets
- Map each speech to its trading day (a weekend speech moves to the next Monday).
- `dy2`: 2-year yield change in basis points, from the previous day's close to the speech day's close. Compute `dy10` and the SPY return the same way.
- `up`: 1 if `dy2 > 0`, else 0.
- Flag speeches on FOMC decision days, CPI release days and jobs-report days. Keep the flag column rather than deleting the rows, so you can show the effect of the filter.

### Step 6 — Event study: does tone move yields?
- Regress `dy2` on `surprise` plus controls with OLS and Newey–West standard errors (`statsmodels`, `cov_type="HAC"`).
- Run it again for Chair-only speeches and for all other speakers. Expect a much larger effect for the Chair.
- One clear chart: average `dy2` by quintile of `surprise`. If tone matters, the bars rise from left to right.

### Step 7 — Predictive models, out of sample
- Train on 2010–2022 and test on 2023 onward. Never shuffle the rows.
- Models: logistic regression, then LightGBM, predicting `up`.
- Baselines: always predict the most common class, and a model using controls only.
- Report accuracy, ROC-AUC and the out-of-sample R² of the regression. The question is whether the text features beat the controls-only baseline.
- Optional: a walk-forward version that refits each year, which is more realistic.

### Step 8 — Chronos-2 benchmark
- Build one daily series for all trading days since 2010: `dy2`, plus two covariates, `speech_score` (the day's average score, 0 if no speech) and `speech_flag` (1 on speech days).
- For each test day *t* from 2023 onward, give Chronos-2 a rolling context (e.g. the last 512 trading days) and forecast one step ahead.
- Run three versions:
  1. Naive: predict 0 change.
  2. Chronos-2 univariate: `dy2` history only.
  3. Chronos-2 with covariates: `speech_score` and `speech_flag` as known future covariates for day *t*, since the speech happens during the day you forecast.
- Compare MAE and directional accuracy **on speech days only**, and also on all days. If version 3 beats version 2 on speech days, the speech carries information the price history does not.
- Compare these results with your step 7 models in one results table.

### Step 9 — Robustness checks
- Placebo test: use the trading day *before* each speech. The effect should vanish. If it does not, something is leaking.
- A 2-day window instead of 1, the raw score instead of the surprise, and the 10-year yield instead of the 2-year.

---

## 4. Repository structure

Keep reusable code in `src/` and the storytelling in `notebooks/`. A recruiter should be able to run the whole pipeline with one command.

```
fedshock/
├── README.md 
├── config.yaml             # dates, train/test cut-off, paths
├── data/
│   ├── raw/                # speeches, market data 
│   ├── processed/          # scored sentences, final event table
│   └── meta/               # speakers.csv, excluded_dates.csv
├── src/
│   ├── collect.py          # BIS + Fed RSS download
│   ├── clean.py            # cleaning, sentence split, keyword filter
│   ├── score.py            # FOMC-RoBERTa scoring + speech score
│   ├── market.py           # FRED + yfinance, targets
│   ├── features.py         # surprise, speaker and control features
│   ├── model.py            # event study + predictive models
│   └── chronos_bench.py    # Chronos-2 rolling forecasts
└── analysis/
│   ├── 01_eda.ipynb
│   ├── 02_event_study.ipynb
│   ├── 03_prediction.ipynb
│   └── 04_chronos_benchmark.ipynb
```

---

## Sources

- [Trillion Dollar Words (Shah, Paturi, Chava, ACL 2023)](https://aclanthology.org/2023.acl-long.368)
- [gtfintechlab/FOMC-RoBERTa model](https://huggingface.co/gtfintechlab/FOMC-RoBERTa)
- [gtfintechlab/fomc-hawkish-dovish code and labelled data](https://github.com/gtfintechlab/fomc-hawkish-dovish)
- [Chronos-2 model card](https://huggingface.co/amazon/chronos-2) and [technical report](https://arxiv.org/abs/2510.15821)
- [BIS central bankers' speeches download](https://www.bis.org/speeches/central-bank/download)
- [istat-ai/cb-speeches dataset](https://huggingface.co/datasets/istat-ai/cb-speeches)
- [Federal Reserve speeches RSS feed](https://www.federalreserve.gov/feeds/speeches.xml)
- [FRED DGS2, 2-year Treasury yield](https://fred.stlouisfed.org/graph?graph_id=484889)

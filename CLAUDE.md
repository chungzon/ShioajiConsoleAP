# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Windows desktop application for Taiwan stock analysis. Tkinter GUI bundles seven feature tabs, talks to 永豐金證券 Shioaji API for live/historical market data, persists daily close prices and K-bars into a local SQL Server (`TSE` database), and additionally exposes a Flask REST API (from inside the GUI's "API服務" tab) for downstream consumers. Runs only on Windows; Python 3.8+. Codebase is mostly Traditional Chinese — match the existing language in comments, logs, and commit messages.

## Run / build / verify

```powershell
pip install -r requirements.txt
python Main.py
# syntax check for a single module after edits (no test runner is wired up):
python -m py_compile model/DailyClosePriceDownloadModel.py
```

There is no `pytest`/`unittest` suite. Files named `test_*.py` at the repo root are standalone scripts run via `python <file>`, not pytest tests. Don't write code that assumes a test framework is in place.

## Architecture: MVC + Main.py wiring

The whole app is wired up in `Main.py:MainApplication.__init__`. It:

1. Logs in to Shioaji (`initialize_api()`),
2. Builds **seven feature triples** — for each feature there is a matching `model/X.py`, `view/X.py`, `controller/X.py`, instantiated as `model = X(api)`, `view = X(tab_control, None, model?)`, `controller = X(model, view)`, then added to the `ttk.Notebook` as a tab,
3. Constructs the API tab (`StockAPIGUIView` — defined inline in `Main.py`),
4. Starts two background schedulers via `app_utils.unified_scheduler_manager` (`start_scheduler` for daily close prices, `start_daily_kbars_scheduler` for K-bars at 17:30).

The seven features and their tabs:

| Tab | Model / View / Controller prefix |
|-----|----------------------------------|
| 資料分析 | `DataAnalysis` |
| 資料下載 | `DataDownload` |
| 即時監控 | `RealtimeMonitor` |
| 資料回測 | `Backtest` |
| 年度交易量下載 | `DailyClosePriceDownload` |
| 選股策略 | `SelectStock` |
| API服務 | `StockAPIGUIView` (inline in Main.py, not in `view/`) |

Models hold business + DB logic. Views are Tkinter `ttk.Frame`s. Controllers route view events to model methods. New features should follow this exact triple convention and be wired in `MainApplication.__init__`.

The Flask API endpoints are **not** in `api/` — they live in `Main.py` inside `StockAPIGUIView.run_api_server`. The `api/ExportJson.py` is the helper used by those endpoints.

## Database

- SQL Server, hardcoded `127.0.0.1:1433`, user `TSE_USER`, database `TSE`. Connection string is in `connect_db()` on each model that needs DB — changing host/credentials means editing those methods. Treat this as a known deployment pain point, not a one-line config.
- `pymssql` driver, autocommit off, transactions explicit.
- Primary table: `stock_data (stock_id VARCHAR(10), date DATE, open_price/high_price/low_price/close_price FLOAT, volume BIGINT, created_at, updated_at)` with PK `(stock_id, date)` and three indexes. `volume` must be `BIGINT` — see migration section.
- `system_config(name, value)` stores `last_download_date` etc.

### Self-healing schema migration

`model/DailyClosePriceDownloadModel.py::ensure_database_structure()` is the central idempotent migration. It runs:

1. In `DailyClosePriceDownloadModel.__init__` (program startup, via `Main.py:1267`),
2. At the start of `download_close_price_by_range()` and `download_daily_close_price()` (defence in depth — entry points other than GUI startup still get checked).

It currently auto-fixes: missing `stock_data` table; `volume INT → BIGINT`; missing PK `(stock_id, date)` (only when there are no `(stock_id, date)` duplicates yet); missing indexes. On failure it `print`s to console *and* writes to log, then aborts the download. **Any future schema change should be added to this function**, not as a one-off SQL the user has to run. Idempotency is the design contract.

Known unhandled case: `ALTER COLUMN volume` fails with SQL error 5074 if a non-clustered index `INCLUDE`s `volume`. The fix pattern (not yet in the code) is *drop dependent index → ALTER → recreate*. Use `sys.index_columns` to discover dependents before altering a column.

## Data sources & their parsing landmines

These bit us repeatedly. If you change the TWSE/TPEx parsers, re-verify these:

- **TPEx CSV footer rows** — `https://www.tpex.org.tw/.../stk_wn1430_result.php` ends with `"共N筆"` and `"ETF證券代號第六碼為K、C者..."`. `csv.DictReader` will parse both as data rows. `is_valid_stock_code()` (ASCII + alphanumeric + len ≤ 10) is the filter — any new code-validation logic must keep these out.
- **TPEx header trailing whitespace** — actual headers are `'收盤 '`, `'開盤 '`, `'最高 '`, `'成交股數  '` (yes, with a trailing space; `'成交股數'` has two). Always `{k.strip(): v ...}` the row before `row.get('收盤')`.
- **TWSE MI_INDEX CSV is multi-section** — slice between `每日收盤行情(全部(不含權證、牛熊證、可展延牛熊證))` and `漲跌(+/-)欄位符號說明:+/-/X表示漲/跌/不比價。`. Adjacent sections like `4.ETF` summary rows must stay outside the slice.
- **TWSE codes come Excel-quoted** — `="2330"` raw; the cleaner is `code.replace('=', '').replace('"', '').strip()`. TPEx codes are plain.
- **Volume overflow is real** — certain ETFs (e.g. `00403A` on 2026-05-12 traded 4.2B shares) exceed `INT` (~2.14B). Always `BIGINT`. This is why the auto-migration exists.
- **tempdb vs TSE collation** — the `#temp_stock_data` table inside `merge_stock_data_batch()` declares `stock_id VARCHAR(10) COLLATE DATABASE_DEFAULT`. Without this, MERGE fails with error 468.

## Connection reuse pattern

`DailyClosePriceDownloadModel` holds `self.conn` / `self.cursor`. Use `self.get_db()` (returns `(conn, cursor)`, recreates if dead) and call `self.close_db()` in a `finally` of the top-level download method. **Don't open a fresh connection per insert call** — this was a hot-path bug that was already fixed; the pattern is the fix. Other models (`DataAnalysisModel`, `DataDownloadModel`, etc.) still open per-call connections — leave those alone unless you're doing the same refactor deliberately.

The MERGE batch in `merge_stock_data_batch()` is the only correct path to write into `stock_data`. It uses a `#temp_stock_data` temp table; with connection reuse, an `IF OBJECT_ID('tempdb..#temp_stock_data') IS NOT NULL DROP` guard at the top of the function protects against leftover temps from a previously aborted call on the same session.

## Schedulers

Two threads start with the app:

- `DataDownloadScheduler` (`DataDownloadScheduler.py`) — daily close prices.
- `DailyKbarsDownloadScheduler` (`DailyKbarsDownloadScheduler.py`) — K-bars at 17:30.

Both register tasks with `app_utils.unified_scheduler_manager.get_unified_scheduler_manager()`, which owns the actual `schedule` thread. Adding a new scheduled job means: write a method, call `scheduler_manager.add_scheduler(name, task_func, schedule_time, task_type)`. Don't spin up a second `schedule.run_pending()` loop.

## House rules

- **Match the surrounding style**: Traditional Chinese comments and log messages, `f"..."` for formatting, `print()` for user-visible status + `self.write_log()` for file log on the same event (the auto-migration prints important events to both).
- **Don't auto-delete user data on the client side.** When `ensure_database_structure()` detects duplicates blocking a PK add, it warns loudly and points at `clean_duplicate_data()` rather than deleting. Preserve that policy for any future destructive migration.
- **Date-range loops skip weekends** (`current.weekday() >= 5`); TWSE/TPEx return nothing on closed days anyway.
- **Don't tracked-down add `venv/` files back in.** `.gitignore` already excludes `venv/`, `__pycache__/`, `logs/`, `shioaji.log`, `.claude/`. Recent history (commit `b12cd6ad`) was specifically a cleanup pass for these.
- **Commit messages are Traditional Chinese**, subject line first then a bullet list body. Use `git commit -F -` heredoc on Bash, or `@'...'@` only when actually running PowerShell — mixing the two will literal-`@` your subject line.

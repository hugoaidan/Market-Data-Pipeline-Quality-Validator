# Market Data Pipeline & Quality Validator

A Python pipeline that reads daily stock price data from a CSV file, validates each row, and stores accepted records in SQLite.

I built this project to practice data validation, database operations, and error handling while developing skills for quantitative development.

## Features

- Checks that all required columns exist.
- Converts dates and numeric fields into usable types.
- Removes leading and trailing whitespace from symbols.
- Normalizes timestamps to calendar dates.
- Reports accepted and rejected row counts and failures by check.
- Stores valid records in SQLite.
- Skips identical records on repeated imports.
- Detects conflicting records without overwriting stored data.
- Rolls back database changes if an import raises a SQLite error.

## Requirements

- Python 3
- pandas 2.0 or newer

SQLite support is included with Python through the `sqlite3` module.

Install pandas:

```bash
pip install "pandas>=2.0"
```

## Input Format

Place a file named `sample_prices.csv` in the directory where you run the script.

Required columns:

| Column | Description |
|--------|-------------|
| symbol | Nonblank stock symbol |
| date | Date or timestamp that pandas can parse |
| open | Opening price |
| high | Highest price |
| low | Lowest price |
| close | Closing price |
| volume | Nonnegative whole-number trading volume |

Example:

```csv
symbol,date,open,high,low,close,volume
TEST,2026-09-14,100,105,99,103,1000
TEST,2026-09-15,103,108,102,107,1200
TEST,2026-09-16,107,108,104,105,900
TEST,2026-09-17,100,105,99,103,1000
```

This example contains two valid rows, one invalid date, and one row whose opening price exceeds its high.

## Running the Pipeline

From the project directory, run:

```bash
python market_data_pipeline.py
```

The script reads `sample_prices.csv` and creates or opens `market_data.db`.

It prints:

- Total, accepted, and rejected row counts.
- Failure counts for each validation check.
- Inserted, skipped, and conflicting record counts.

For the example above, the first run with an empty database should accept two rows, reject two rows, and insert two records. Running the same file again should skip the two existing records.

## Validation Rules

Rows are rejected when they contain:

- Missing or unparseable dates.
- Missing or blank symbols.
- Missing or nonnumeric prices or volume.
- Infinite numeric values.
- Prices less than or equal to zero.
- Opening or closing prices outside the low–high range.
- Negative or fractional volume.
- Duplicate symbol-and-date pairs within the input file.

All occurrences of an input duplicate are rejected. Timestamps are normalized to calendar dates before checking for duplicates.

A row can fail multiple checks, so the sum of failure counts may exceed the number of rejected rows.

## Database and Repeated Imports

Valid records are stored in the `daily_prices` table. The combination of `symbol` and `date` is its primary key.

Each accepted input record is handled as follows:

| Situation | Action |
|-----------|--------|
| Symbol and date do not exist | Insert the record |
| Symbol and date exist with identical values | Skip the record |
| Symbol and date exist with different values | Report a conflict and preserve the stored record |

“Accepted” means a row passed validation. It does not necessarily mean the row was newly inserted.

## Error Handling

The pipeline handles missing files, empty CSV files, CSV parsing errors, database connection errors, and SQLite errors during import.

If a database import fails, pending changes are rolled back and the connection is closed.

## Current Limitations

- Input and database filenames are fixed in the script.
- Designed for daily stock prices with dates that have no timezone offsets.
- Symbols are case-sensitive.
- Input prices must use consistent units and adjustment conventions.
- Validation checks internal consistency; it does not verify prices against an external market data source.
- Rejected rows and their validation results are not exported to a separate file.

## Future Improvements

- Command-line arguments for input and database paths.
- Export rejected rows with their failure reasons.
- Automated regression tests.
- Download market data from an external provider.
- Query stored prices by symbol and date range.

## Technologies

- Python
- pandas
- SQLite

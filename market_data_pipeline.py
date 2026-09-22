import sqlite3 as sq
import pandas as pd

df = pd.read_csv('sample_prices.csv')
columns = ['symbol','date','open','high','low','close','volume']
numeric_columns = ['open','high','low','close','volume']

def column_check(columns, df):
    missing_col = []
    for column in columns:
        if column not in df.columns:
            missing_col.append(column)
    return missing_col

def normalize_data(df):
    new_date = pd.to_datetime(df["date"], errors="coerce")
    df["date"] = new_date

    for column in numeric_columns:
        new = pd.to_numeric(df[column], errors="coerce")
        df[column] = new

    empty_symbol = df["symbol"].str.strip()
    df["symbol"] = empty_symbol

    return df

def validation(df):
    inv_dates = df["date"].isna()
    inv_columns = df[numeric_columns].isna()
    inv_numeric_rows = inv_columns.any(axis=1)

    inv_open_high = df["open"] > df["high"]
    inv_open_low = df["open"] < df["low"]
    inv_close_high = df["close"] > df["high"]
    inv_close_low = df["close"] < df["low"]
    inv_prices = inv_open_high | inv_open_low | inv_close_high | inv_close_low

    inv_volume = df["volume"] < 0

    blank_symbols = df["symbol"] == ""
    inv_symbols = blank_symbols | df["symbol"].isna()

    duplicate_columns = ['symbol', 'date']
    inv_duplicates = df[duplicate_columns].duplicated(keep=False)

    check = {"invalid_dates": inv_dates, "invalid_symbols": inv_symbols, "invalid_numeric": inv_numeric_rows, "invalid_prices": inv_prices, "negative_volume": inv_volume, "duplicate": inv_duplicates}
    validation_report = pd.DataFrame(data=check)

    return validation_report

missing = column_check(columns, df)

if len(missing) == 0:
    df = normalize_data(df)
    validation_report = validation(df)
    inv_rows = validation_report.any(axis=1)
    rejected_rows = df[inv_rows]
    val_rows = df[~inv_rows]
    failures = validation_report.sum(axis=0)
else:
    print(f"{missing} columns are missing.")

connection = sq.connect("market_data.db")

create_table_sql = ("CREATE TABLE IF NOT EXISTS daily_prices (symbol TEXT NOT NULL, date TEXT NOT NULL, volume INTEGER NOT NULL, "
"close REAL NOT NULL, open REAL NOT NULL, high REAL NOT NULL, low REAL NOT NULL, PRIMARY KEY (symbol, date))")

connection.execute(create_table_sql)

insert_sql = ("INSERT INTO daily_prices (symbol, date, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?)")

rows_to_store = val_rows.copy()

new_rows = rows_to_store["date"].dt.strftime("%Y-%m-%d")
rows_to_store["date"] = new_rows

ordered_rows = rows_to_store[columns]
records = ordered_rows.itertuples(index=False, name=None)

connection.executemany(insert_sql, records)
connection.commit()

select_sql = "SELECT * FROM daily_prices"
cursor = connection.execute(select_sql)
stored_rows = cursor.fetchall()
print(stored_rows)
connection.close()

import sqlite3 as sq

import pandas as pd

columns = ['symbol','date','open','high','low','close','volume']
numeric_columns = ['open','high','low','close','volume']

def column_check(columns, df):
    missing_col = []
    for column in columns:
        if column not in df.columns:
            missing_col.append(column)
    return missing_col

def normalize_data(df):
    new_date = pd.to_datetime(df["date"], errors="coerce", format="mixed")
    df["date"] = new_date.dt.normalize()

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

    price_columns = ['open', 'high', 'low', 'close']
    inv_nonpositive_prices = (df[price_columns] <= 0).any(axis=1)

    inv_infinite = (df[numeric_columns].isin([float("inf"), float("-inf")])).any(axis=1)

    inv_fractional_volume = ((df["volume"] % 1 != 0) & df["volume"].notna() & ~df["volume"].isin([float("inf"), float("-inf")]))

    check = {"invalid_dates": inv_dates, "invalid_symbols": inv_symbols, "invalid_numeric": inv_numeric_rows, "invalid_prices": inv_prices, "negative_volume": inv_volume, 
             "duplicate": inv_duplicates, "nonpositive_prices": inv_nonpositive_prices, "infinite_numeric": inv_infinite, "fractional_volume": inv_fractional_volume}
    validation_report = pd.DataFrame(data=check)

    return validation_report

def import_records(connection, records):
    insert_sql = ("INSERT INTO daily_prices (symbol, date, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?)")
    lookup_sql = ("SELECT symbol, date, open, high, low, close, volume FROM daily_prices WHERE symbol = ? AND date = ?")
    skipped = 0
    inserted = 0
    conflicts = 0

    for record in records:
        lookup_values = (record[0], record[1])
        cursor = connection.execute(lookup_sql, lookup_values)
        existing_record = cursor.fetchone()

        if existing_record is None:
            connection.execute(insert_sql, record)
            inserted += 1
        elif existing_record == record:
            skipped += 1
        else:
            print(f"ERROR, conflict for {record[0]} and {record[1]}")
            conflicts += 1
    
    return inserted, skipped, conflicts


def main(): 
    try:
        df = pd.read_csv('sample_prices.csv', dtype={"symbol" : "string"})
    except FileNotFoundError as error:
        print(f"ERROR, {error}")
        return
    except pd.errors.EmptyDataError as error:
        print(f"CSV file is empty or has no header, {error}")
        return
    except pd.errors.ParserError as error: 
        print(f"CSV could not be parsed, {error}")
        return

    missing = column_check(columns, df)
    if len(missing) == 0:
        df = normalize_data(df)
        validation_report = validation(df)
        inv_rows = validation_report.any(axis=1)
        rejected_rows = df[inv_rows]
        val_rows = df[~inv_rows]
        failures = validation_report.sum(axis=0)
        print(f"Total Rows: {len(df)}\nAccepted Rows: {len(val_rows)}\nRejected Rows: {len(rejected_rows)}\nFailures by check: {failures}\n")
    else:
        print(f"{missing} columns are missing.")
        return

    rows_to_store = val_rows.copy()
    new_rows = rows_to_store["date"].dt.strftime("%Y-%m-%d")
    rows_to_store["date"] = new_rows
    ordered_rows = rows_to_store[columns]
    records = ordered_rows.itertuples(index=False, name=None)

    try:
        connection = sq.connect('market_data.db')
    except sq.Error as error:
        print(f"ERROR, {error}")
        return

    create_table_sql = ("CREATE TABLE IF NOT EXISTS daily_prices (symbol TEXT NOT NULL, date TEXT NOT NULL, volume INTEGER NOT NULL, "
    "close REAL NOT NULL, open REAL NOT NULL, high REAL NOT NULL, low REAL NOT NULL, PRIMARY KEY (symbol, date))")

    try:
        connection.execute(create_table_sql)
        inserted, skipped, conflicts = import_records(connection, records)
        connection.commit()
    except sq.Error as error:
        connection.rollback()
        print(f"ERROR, {error}")
    else: 
        print(f"Inserted: {inserted}\nSkipped: {skipped}\nConflicts: {conflicts}")
    finally:
        connection.close()

if __name__ == "__main__":
    main()
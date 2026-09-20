import pandas as pd

df = pd.read_csv('sample_prices.csv')
columns = ['symbol','date','open','high','low','close','volume']

def column_check(columns, df):
    missing_col = []
    for column in columns:
        if column not in df.columns:
            missing_col.append(column)
    return missing_col

missing = column_check(columns, df)

if len(missing) == 0:
    print("Column check passed!")
else:
    print(f"{missing} columns are missing.")
    
new_date = pd.to_datetime(df["date"], errors="coerce")
df["date"] = new_date
inv_dates = df["date"].isna()
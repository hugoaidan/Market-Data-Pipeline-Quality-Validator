import pandas as pd

df = pd.read_csv('sample_prices.csv')
columns = ['symbol','date','open','high','low','close','volume']

def column_check(columns, df):
    missing_col = []
    for column in columns:
        if column not in df.columns:
            missing_col.append(column)
    return missing_col
    
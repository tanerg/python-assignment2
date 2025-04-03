import pandas as pd

def load_cleaned_data(filepath):
    df = pd.read_csv(filepath, parse_dates=['Date'])
    df['Year'] = df['Year'].astype(int)
    df['Month'] = df['Date'].dt.month
    return df
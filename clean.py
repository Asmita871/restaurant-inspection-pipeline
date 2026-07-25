import pandas as pd

def load_and_clean(raw_path):
    df = pd.read_csv(raw_path)
    df_clean = df.drop_duplicates().copy()
    df_clean['BORO'] = df_clean['BORO'].replace('0', 'Unknown')
    df_clean['INSPECTION DATE'] = pd.to_datetime(df_clean['INSPECTION DATE'], errors='coerce')
    df_recent = df_clean[df_clean['INSPECTION DATE'].dt.year >= 2022].copy()
    return df_recent

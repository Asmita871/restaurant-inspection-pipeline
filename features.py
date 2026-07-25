import pandas as pd

def build_features(df_recent):
    establishment_features = df_recent.groupby('CAMIS').agg(
        dba=('DBA', 'first'),
        boro=('BORO', 'first'),
        cuisine=('CUISINE DESCRIPTION', 'first'),
        total_inspections=('CAMIS', 'count'),
        total_critical=('CRITICAL FLAG', lambda x: (x == 'Critical').sum()),
        avg_score=('SCORE', 'mean'),
    ).reset_index()
    establishment_features['critical_rate'] = (
        establishment_features['total_critical'] / establishment_features['total_inspections']
    )
    return establishment_features

from fastapi import FastAPI
import pandas as pd

app = FastAPI()
establishment_features = pd.read_csv("establishment_features.csv")

@app.get("/establishment/{camis_id}")
def get_establishment(camis_id: int):
    row = establishment_features[establishment_features['CAMIS'] == camis_id]
    if row.empty:
        return {"error": "not found"}
    return row.iloc[0].to_dict()

@app.get("/check-anomaly/{camis_id}")
def check_anomaly(camis_id: int, new_critical_count: int):
    row = establishment_features[establishment_features['CAMIS'] == camis_id]
    if row.empty:
        return {"error": "not found"}
    r = row.iloc[0]
    avg = r['total_critical'] / max(r['total_inspections'], 1)
    flagged = new_critical_count > avg * 2
    return {"establishment": r['dba'], "historical_avg": round(avg,2), "flagged": bool(flagged)}

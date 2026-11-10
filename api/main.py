"""Serves the 4-week forecasts written by the notebook (artifacts/forecasts.parquet)."""
import os
from datetime import date

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

FORECAST_FILE = os.getenv("FORECAST_FILE", "artifacts/forecasts.parquet")
forecasts = pd.read_parquet(FORECAST_FILE)

app = FastAPI(title="Walmart 4-week sales forecast", version="1.0")


class Week(BaseModel):
    week_ending: date
    p10: float
    p50: float
    p90: float


class Forecast(BaseModel):
    store: int
    dept: int
    weeks: list[Week]
    stock_4_weeks_p75: float
    stock_4_weeks_p90: float


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "series": int(forecasts.groupby(["Store", "Dept"]).ngroups),
            "first_week": str(forecasts["Date"].min().date()), "last_week": str(forecasts["Date"].max().date())}


@app.get("/forecast/{store}/{dept}", response_model=Forecast)
def forecast(store: int, dept: int) -> Forecast:
    rows = forecasts[(forecasts["Store"] == store) & (forecasts["Dept"] == dept)].sort_values("Date")
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"No forecast for store {store}, dept {dept}")
    weeks = [Week(week_ending=r.Date.date(), p10=round(r.p10, 2), p50=round(r.p50, 2), p90=round(r.p90, 2))
             for r in rows.itertuples()]
    return Forecast(store=store, dept=dept, weeks=weeks,
                    stock_4_weeks_p75=round(rows["stock_p75"].iloc[0], 2),
                    stock_4_weeks_p90=round(rows["stock_p90"].iloc[0], 2))

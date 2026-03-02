from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import json
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi import Query
from typing import Optional
from math import floor

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# declaring the directory name we want to use
templates = Jinja2Templates(directory="templates")
 
DATA_DIR = Path(__file__).parent / "dataset"
Flights_Data = DATA_DIR / "airplane_flights_1day.geojson"


def load_data():
    global flightdata
    with open(Flights_Data, "r") as f:
        flightdata = json.load(f)

load_data()

# Helper functions moved server-side
TEN_MINUTES_MS = 1000 * 60 * 10

def compute_time_range():
    min_t = float('inf')
    max_t = float('-inf')
    for feat in flightdata.get('features', []):
        props = feat.get('properties', {})
        st = props.get('startTime')
        et = props.get('endTime')
        if st is not None:
            min_t = min(min_t, st)
        if et is not None:
            max_t = max(max_t, et)
    if min_t == float('inf'):
        return None
    total_steps = (max_t - min_t) // TEN_MINUTES_MS
    return {"minTime": int(min_t), "maxTime": int(max_t), "tenMinSteps": int(total_steps)}

def interpolate_position(coords, progress: float):
    # coords: list of [lon, lat, alt]
    n = len(coords)
    if n == 0:
        return None
    if n == 1:
        return coords[0]
    # clamp progress
    p = max(0.0, min(1.0, progress))
    target = p * (n - 1)
    idx = int(floor(target))
    if idx >= n - 1:
        return coords[-1]
    t = target - idx
    a = coords[idx]
    b = coords[idx + 1]
    lon = a[0] + (b[0] - a[0]) * t
    lat = a[1] + (b[1] - a[1]) * t
    alt = None
    try:
        alt = int(a[2] + (b[2] - a[2]) * t)
    except Exception:
        alt = 0
    return [lon, lat, alt]

async def api_time_range():
    tr = compute_time_range()
    if not tr:
        return JSONResponse({"error": "no data"}, status_code=404)
    return JSONResponse(tr)


@app.get('/api/positions')
async def api_positions(step: Optional[int] = Query(None), time_ms: Optional[int] = Query(None)):
    # Accept either step (number of 10-min intervals since minTime) or explicit time_ms
    tr = compute_time_range()
    if not tr:
        return JSONResponse({"features": []})
    min_t = tr['minTime'] 
    if step is not None:
        current_time = min_t + int(step) * TEN_MINUTES_MS
    elif time_ms is not None:
        current_time = int(time_ms)
    else:
        current_time = min_t

    features = []
    for feat in flightdata.get('features', []):
        props = feat.get('properties', {})
        st = props.get('startTime')
        et = props.get('endTime')
        if st is None or et is None:
            continue
        if st <= current_time <= et:
            duration = et - st
            elapsed = current_time - st
            progress = max(0.0, min(1.0, elapsed / duration)) if duration > 0 else 1.0
            pos = interpolate_position(feat['geometry']['coordinates'], progress)
            # next point for client-side bearing (turf.js)
            n = len(feat['geometry']['coordinates'])
            target = progress * (n - 1)
            idx = int(floor(target))
            next_idx = min(idx + 1, n - 1)
            next_pt = feat['geometry']['coordinates'][next_idx]
            next_position = [next_pt[0], next_pt[1]] if next_pt else None
            new_feat = {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": pos},
                "properties": {**props, "progress": progress, "nextPosition": next_position}
            }
            features.append(new_feat)

    return JSONResponse({"type": "FeatureCollection", "features": features})

@app.get('/')
async def name(request: Request):
    global flightdata
    with open(Flights_Data, "r") as f:
        flightdata = json.load(f)
        return templates.TemplateResponse("index.html", {"request": request, "housedata": flightdata}) 
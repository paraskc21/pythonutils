from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import json
from pathlib import Path
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# declaring the directory name we want to use
templates = Jinja2Templates(directory="templates")
 
DATA_DIR = Path(__file__).parent / "dataset"
China_Houses = DATA_DIR / "airplane_flights.geojson"


def load_data():
    global housedata
    with open(China_Houses, "r") as f:
        housedata = json.load(f)

load_data()

@app.get('/')
async def name(request: Request):
    global housedata
    with open(China_Houses, "r") as f:
        housedata = json.load(f)
        return templates.TemplateResponse("index.html", {"request": request, "housedata": housedata}) 
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn, pygame
from PIL import Image, ImageChops, ImageFilter
import chess
import random
import numpy as np

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

try:
    with open("counter.txt", "r") as file:
        image_counter = int(file.read())
except FileNotFoundError:
    image_counter = 0
image_counter = 0
def get_next_image():
    global image_counter
    # Construire le chemin du prochain fichier image en incrémentant le compteur
    image_path = f"image_{image_counter}.jpg"
    # Incrémenter le compteur pour la prochaine fois
    print(image_counter)
    image_counter += 1
    with open("counter.txt", "w") as file:
        file.write(str(image_counter))
    return image_path

@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
    image_path = get_next_image()
    return templates.TemplateResponse("index.html", {"request": request, "imagePath":image_path})

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)








"""def calculerCoupSuivant():
    return FileResponse("Documents/L1/image0.jpg")


app = FastAPI()



app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get('/nextMove')
async def home(request: Request):
    path = calculerCoupSuivant()
    return FileResponse(path)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)"""

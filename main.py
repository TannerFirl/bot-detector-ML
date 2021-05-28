

from fastapi import FastAPI

from classes.Player import Player
from model.train import train_model

# run a job every hour
# JOB:
def job():
    # get players & hiscore data to predict from API
    #   preprocess
    #   predict
    #   post predictions to API
    pass

app = FastAPI()
db =[]

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/predictions")
def get_prediction(player: Player):
    # receive data
    # preprocessing
    # return prediction
    print(player)
    db.append(player.dict())
    return db[-1]

@app.post("/train-model")
def train():
    train_model()
    return {'OK':'OK'}

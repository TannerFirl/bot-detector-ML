import asyncio
import logging
from math import log

import aiohttp
import requests

from config import app, detector_api, token
from MachineLearning.data import data_class
from MachineLearning.model import model

LABELS = [
    'Real_Player', 'Smithing_bot', 'Mining_bot', 
    'Magic_bot', 'PVM_Ranged_bot',  
    'Fletching_bot', 'PVM_Melee_bot', 'Herblore_bot',
    'Thieving_bot','Crafting_bot', 'PVM_Ranged_Magic_bot',
    'Hunter_bot','Runecrafting_bot','Fishing_bot','Agility_bot',
    'Cooking_bot', 'mort_myre_fungus_bot', 
    'Woodcutting_bot', 'Fishing_Cooking_bot',
    'Agility_Thieving_bot', 'Construction_Magic_bot','Construction_Prayer_bot',
    'Zalcano_bot'
]

ml = model(LABELS)

async def loop_request(BASE_URL, json, debug=True):
    i, data = 1, []

    while True:
        # build url
        url = f'{BASE_URL}&row_count=100000&page={i}'

        # logging
        logging.debug(f'Request: {url=}')

        # make reqest
        res = requests.post(url, json=json)

        # break condition
        if not res.status_code == 200:
            logging.debug(f'Break: {res.status_code=}, {url=}')
            break
        
        # parse data
        res = res.json()
        data += res

        # break condition
        if len(res) == 0:
            logging.debug(f'Break: {len(res)=}, {url=}')
            break
        
        # logging (after break)
        logging.debug(f'Succes: {len(res)=}, {len(data)=} {i=}')

        # update iterator
        i += 1
    return data

@app.on_event('startup')
async def initial_task():

    # loop = asyncio.get_running_loop()
    # loop.create_task(get_player_hiscores())
    return

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/infinite-predict")
async def train():
    asyncio.create_task(get_player_hiscores())
    return {'ok': 'ok'}

@app.get("/load")
async def train():
    if ml.model is None:
        ml.model = ml.load('model')
    return {'ok': 'ok'}

@app.get("/train")
async def train():
    #TODO: verify token


    # request labels
    url = f'{detector_api}/v1/label?token={token}'

    # logging
    logging.debug(f'Request: {url=}')
    data = requests.get(url).json()

    # filter labels
    labels = [d for d in data if d['label'] in LABELS]
    
    # memory cleanup
    del url, data

    # create an input dict for url
    label_input = {}
    label_input['label_id'] = [l['id'] for l in labels]
    
    # request all player with label
    url = f'{detector_api}/v1/player/bulk?token={token}'
    data = await loop_request(url, label_input)

    # players dict
    players = data

    # memory cleanup
    del url, data

    # get all player id's
    player_input = {}
    player_input['player_id'] = [int(p['id']) for p in players]

    # request hiscore data latest with player_id
    url = f'{detector_api}/v1/hiscore/Latest/bulk?token={token}'
    data = await loop_request(url, player_input)

    # hiscores dict
    hiscores = data_class(data)

    # memory cleanup
    del url, data

    ml.train(players, labels, hiscores)
    # memory cleanup
    del players, labels, hiscores
    return {'ok': 'ok'}

async def get_player_hiscores():
    logging.debug('getting data')
    url = f'{detector_api}/v1/prediction/data?token={token}'
    logging.debug(url)
    data = requests.get(url).json()

    # if there is no data wait and try to see if there is new data
    if len(data) == 0:
        logging.debug('no data to predict')
        await asyncio.sleep(600)
        return asyncio.create_task(get_player_hiscores())

    # clean & filter data
    data = data_class(data)

    # make predictions
    predictions = ml.predict(data)
    #TODO: combine user_id with prediction

    # post predictions
    #TODO: post prediction to api
    return asyncio.create_task(get_player_hiscores())
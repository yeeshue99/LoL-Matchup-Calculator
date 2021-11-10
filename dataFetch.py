import requests
from settings import *

def getPatchData():
    r = requests.get(url = PATCHES_JSON_URL)
    data = r.json()
    return data

def getLastFivePatches(region):
    data = getPatchData()
    patches = data['patches']
    offset = data['shifts'][region]
    lastFivePatches = patches[-5:]
    return lastFivePatches, offset

def getStartTimeOfFifthLastPatch(region):
    data, offset = getLastFivePatches(region)
    return data[0]['start'], offset

def calculateStartTime(region = REGION):
    data, offset = getStartTimeOfFifthLastPatch(region)
    return data + offset

def downloadChampionBasicData():
    r = requests.get(url = CHAMPION_DATA_URL)
    data = r.json()
    with open(CHAMPION_DATA_FILE, 'wb') as filehandle:
        import json
        json.dump(data, filehandle)
    
if __name__ == '__main__':
    print(calculateStartTime())
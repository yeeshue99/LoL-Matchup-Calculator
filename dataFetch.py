import requests
from settings import *

def getPatchData():
    r = requests.get(url = PATCHES_JSON_URL)
    data = r.json()
    return data

def getLastNumberPatches(region, number):
    data = getPatchData()
    patches = data['patches']
    offset = data['shifts'][region]
    lastFivePatches = patches[-number:]
    return lastFivePatches, offset

def getStartTimeOfFifthLastPatch(region, number):
    data, offset = getLastNumberPatches(region, number)
    return data[0]['start'], offset

def calculateStartTime(region = REGION, number = 5):
    data, offset = getStartTimeOfFifthLastPatch(region, number)
    return data + offset

def downloadChampionBasicData():
    r = requests.get(url = CHAMPION_DATA_URL)
    data = r.json()
    with open(CHAMPION_DATA_FILE, 'wb') as filehandle:
        import json
        json.dump(data, filehandle)
    
if __name__ == '__main__':
    print(calculateStartTime())
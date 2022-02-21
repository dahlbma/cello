import requests
import json

baseUrl = 'http://esox3.scilifelab.se:8084/'

def listify(data, addBlank=True):
    res = data.content.decode()
    res = json.loads(res)
    cleanList = list()
    if addBlank:
        cleanList.append(None)
    for i in res:
        cleanList.append(i[0])
    return cleanList

def login(user, password, database):
    r = requests.post(f'{baseUrl}login',
                      data = {'username':user,
                              'password':password,
                              'database':database})
    return r

def getDatabase():
    r = requests.get(f'{baseUrl}getDatabase')
    res = listify(r, False)
    return res

def getVialInfo(token, vialId):
    r = requests.get(f'{baseUrl}vialInfo/{vialId}',
            headers={'token':token})
    try:
        return r.content.decode()
    except:
        return r.content

def getLocationsByStorage(token, storage):
    r = requests.get(f'{baseUrl}getLocationByStorage/{storage}',
                     headers={'token':token})
    try:
        res = r.content.decode()
        res = json.loads(res)
        return res
    except:
        return r.content
    
def getBatches(token, batchIds):
    r = requests.get(f'{baseUrl}searchBatches/{batchIds}',
            headers={'token':token})
    try:
        return r.content.decode()
    except:
        return r.content

def getManyVials(token, vialIds):
    r = requests.get(f'{baseUrl}searchVials/{vialIds}',
            headers={'token':token})
    try:
        return r.content.decode()
    except:
        return r.content

def printBoxLabel(token, sBox):
    r = requests.get(f'{baseUrl}printBox/{sBox}',
                     headers={'token': token})
    res = r.content.decode()
    return res

def printVialLabel(token, sVial):
    r = requests.get(f'{baseUrl}printVial/{sVial}',
                     headers={'token': token})
    res = r.content.decode()
    return res

def getFreePositions(token):
    r = requests.get(f'{baseUrl}getFreeBoxes',
                     headers={'token': token})
    res = r.content.decode()
    return res

def createMolImage(token, vialOrCompound):
    r = requests.get(f'{baseUrl}createMolImage/{vialOrCompound}',
                     headers={'token': token})
    res = r.content.decode()
    return res

def getMolImage(vialOrCompound):
    r = requests.get(f'{baseUrl}mols/{vialOrCompound}.png')
    res = r.content
    return res

def getBox(token, box):
    r = requests.get(f'{baseUrl}getBox/{box}',
                     headers={'token': token})
    try:
        res = r.content.decode()
    except:
        res = r.content
    return res

def getBoxLocation(token, box):
    r = requests.get(f'{baseUrl}getBoxLocation/{box}',
                     headers={'token': token})
    try:
        res = r.content.decode()
    except:
        res = r.content
    return res

def updateVialPosition(token, vial, box, pos):
    r = requests.put(f'{baseUrl}updateVialPosition/{vial}/{box}/{pos}',
                     headers={'token': token})
    if r.status_code != 200:
        return False
    else:
        return True

def transitVials(token, vials):
    r = requests.put(f'{baseUrl}transitVials/{vials}',
                      headers={'token': token})
    if r.status_code != 200:
        return False
    else:
        return True

def getLocationChildren(token, location):
    r = requests.get(f'{baseUrl}getLocationChildren/{location}',
                     headers={'token': token})
    try:
        res = r.content.decode()
    except:
        res = r.content
    return res

def addBox(token, sParent, sBoxName, sBoxSize):
    r = requests.put(f'{baseUrl}addBox/{sParent}/{sBoxName}/{sBoxSize}',
                      headers={'token': token})
    if r.status_code != 200:
        return False
    else:
        return True

def addLocation(token, sParent, sLocationName, sLocationType):
    r = requests.put(f'{baseUrl}addLocation/{sParent}/{sLocationName}/{sLocationType}',
                      headers={'token': token})
    if r.status_code != 200:
        return False
    else:
        return True

def deleteLocation(token, location):
    r = requests.put(f'{baseUrl}deleteLocation/{location}',
                      headers={'token': token})
    if r.status_code != 200:
        return r, False
    else:
        return r, True

def getMicroTubeByBatch(token, batches):
    r = requests.get(f'{baseUrl}getMicroTubeByBatch/{batches}',
                      headers={'token': token})
    try:
        res = r.content.decode()
    except:
        res = r.content
    return res

    #{
    #    "batchId": "305055385",
    #    "tubeId": "2004959484",
    #    "volume": 200.0,
    #    "matrixId": "MX6282",
    #    "position": "C04",
    #    "location": "LCBKI_SLL/A4590_CDC/KIWI/Inside KIWI"
    #},

def getRack(token, rack):
    r = requests.get(f'{baseUrl}getRack/{rack}',
                      headers={'token': token})
    try:
        res = r.content.decode()
    except:
        res = r.content
    return res
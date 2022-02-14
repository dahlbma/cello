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

def getFreePositions(token):
    r = requests.get(f'{baseUrl}getFreeBoxes',
                     headers={'token': token})
    res = r.content.decode()
    return res

def createMolImage(token, vial):
    r = requests.get(f'{baseUrl}createMolImage',
                     params={'vial': vial},
                     headers={'token': token})
    res = r.content.decode()
    return res

def getMolImage(vial):
    r = requests.get(f'{baseUrl}mols/{vial}.png')
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

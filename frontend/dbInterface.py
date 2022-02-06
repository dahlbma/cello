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

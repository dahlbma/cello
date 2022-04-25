import requests
import json

baseUrl = 'http://esox3.scilifelab.se:8084/'

def listify(data, addBlank=True):
    res = data.content.decode()
    res = json.loads(res)
    cleanList = list()
    if addBlank:
        cleanList.append(' ')
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

def uploadBinary(token, os_name, file):
    r = requests.post(f'{baseUrl}uploadBinary',
                      data = {'os_name':os_name},
                      headers = {'token':token},
                      files = {'file':file})
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def getCelloBinary(os_name):
    r = requests.get(f'{baseUrl}getCelloBinary/{os_name}',
                     stream=True) # fetch cello dist
    return r

def getVersion():
    r = requests.get(f'{baseUrl}getVersionData') # get file version
    return r

def uploadVersionNo(token, ver_no):
    r = requests.post(f'{baseUrl}getVersionData',
                      data = {'ver_no':ver_no},
                      headers = {'token':token}) # get file version
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def getVialInfo(token, vialId):
    r = requests.get(f'{baseUrl}vialInfo/{vialId}',
            headers={'token':token})
    try:
        return r.content.decode()
    except:
        return r.content

def verifyVial(token, vialId):
    r = requests.get(f'{baseUrl}verifyVial/{vialId}',
            headers={'token':token})
    try:
        return r.content.decode()
    except:
        return r.content
    
def editVial(token,
             sVial,
             batch_id,
             tare,
             iGross,
             iNetWeight,
             conc):
    r = requests.post(f'{baseUrl}editVial',
                      data = {'sVial': sVial,
                              'batch_id': batch_id,
                              'tare': tare,
                              'iGross': iGross,
                              'iNetWeight': iNetWeight,
                              'conc': conc},
                      headers = {'token':token})
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        res = r.content.decode()
        res = json.loads(res)
        return res, True

def uploadTaredVials(token, file):
    r = requests.post(f'{baseUrl}uploadTaredVials',
                     headers={'token': token},
                     files={'file':file})
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True


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

def printPlateLabel(token, sPlate):
    r = requests.get(f'{baseUrl}printPlate/{sPlate}',
                     headers={'token': token})
    res = r.content.decode()
    return res

def getFreePositions(token):
    r = requests.get(f'{baseUrl}getFreeBoxes',
                     headers={'token': token})
    res = r.content.decode()
    return res

def createMolImage(token, sId):
    r = requests.get(f'{baseUrl}createMolImage/{sId}',
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

def getLocationPath(token, location):
    r = requests.get(f'{baseUrl}getLocationPath/{location}',
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

def getMicroTubes(token, batches):
    r = requests.get(f'{baseUrl}getMicroTubes/{batches}',
                      headers={'token': token})
    try:
        res = r.content.decode()
    except:
        res = r.content
    return res

def getRack(token, rack):
    r = requests.get(f'{baseUrl}getRack/{rack}',
                      headers={'token': token})
    try:
        res = r.content.decode()
    except:
        res = r.content
    return res

def verifyLocation(token, location):
    r = requests.get(f'{baseUrl}verifyLocation/{location}',
                      headers={'token': token})
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def createRacks(token, name, nr_o_rs):
    r = requests.put(f'{baseUrl}createRacks/{name}/{nr_o_rs}',
                      headers={'token':token})
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True
    
def readScannedRack(token, location, file):
    r = requests.post(f'{baseUrl}readScannedRack',
                      headers={'token': token},
                      data={'location': location},
                      files={'file':file})
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def updateRackLocation(token, rack_id, box_id):
    r = requests.put(f'{baseUrl}updateRackLocation/{rack_id}/{box_id}',
                      headers={'token':token})
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def addMicrotube(token, tubeId, compBatch, volume, conc):
    r = requests.put(f'{baseUrl}addMicrotube/{tubeId}/{compBatch}/{volume}/{conc}',
                      headers={'token': token})
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def verifyPlate(token, plate):
    r = requests.get(f'{baseUrl}verifyPlate/{plate}',
                      headers={'token':token})
    if r.status_code != 200:
        return r.content.decode(), 0
    else:
        return r.content.decode(), 1


def createPlates(token, type, name, nr_o_ps):
    r = requests.put(f'{baseUrl}createPlates/{type}/{name}/{nr_o_ps}',
                      headers={'token':token})
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def getPlate(token, plate):
    r = requests.get(f'{baseUrl}getPlate/{plate}',
                      headers={'token': token})
    try:
        res = r.content.decode()
    except:
        res = r.content
    return res

def updatePlateName(token, plate, comment):
    r = requests.put(f'{baseUrl}updatePlateName/{plate}/{comment}',
                      headers={'token':token})
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def mergePlates(token, q1, q2, q3, q4, target, volume):
    r = requests.post(f'{baseUrl}mergePlates',
                      data = {
                          'q1': q1,
                          'q2': q2,
                          'q3': q3,
                          'q4': q4,
                          'target': target,
                          'volume':volume},
                      headers={'token':token})
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True


def uploadWellInformation(token,
                          plate_id,
                          well,
                          compound_id,
                          batch,
                          form,
                          conc,
                          volume):
    r = requests.post(f'{baseUrl}uploadWellInformation',
                      data = {'plate_id':plate_id,
                              'well':well,
                              'compound_id':compound_id,
                              'batch':batch,
                              'form':form,
                              'conc':conc,
                              'volume':volume},
                      headers={'token':token})
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def discardVial(token, vial_id):
    r = requests.put(f'{baseUrl}discardVial/{vial_id}',
                      headers={'token': token})
    if r.status_code != 200:
        return r, False
    else:
        return r, True

def discardPlate(token, plate_id):
    r = requests.put(f'{baseUrl}discardPlate/{plate_id}',
                      headers={'token': token})
    if r.status_code != 200:
        return r, False
    else:
        return r, True
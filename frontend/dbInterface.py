import requests
import json
import ast
import warnings

warnings.filterwarnings('ignore')

# CHANGE THIS
# database base URL
baseUrl = 'https://esox3.scilifelab.se/vialdb/'
#baseUrl = 'http://esox3.scilifelab.se:8082/'

# communication handles, check database handler in /backend/ for request handling details

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
                              'database':database}, verify=False)
    return r

def getDatabase():
    r = requests.get(f'{baseUrl}getDatabase', verify=False)
    res = listify(r, False)
    return res

def uploadBinary(token, os_name, file):
    r = requests.post(f'{baseUrl}uploadBinary',
                      data = {'os_name':os_name},
                      headers = {'token':token},
                      files = {'file':file}, verify=False)
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def getCelloBinary(os_name):
    r = requests.get(f'{baseUrl}getCelloBinary/{os_name}',
                     stream=True, verify=False) #fetch cello dist
    return r

def getVersion():
    r = requests.get(f'{baseUrl}getVersionData', verify=False) #get file version
    return r

def uploadVersionNo(token, ver_no):
    r = requests.post(f'{baseUrl}uploadVersionNo',
                      data = {'ver_no':ver_no},
                      headers = {'token':token}, verify=False) #set file version
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def uploadLauncher(token, os_name, file):
    r = requests.post(f'{baseUrl}uploadLauncher',
                      data = {'os_name':os_name},
                      headers = {'token':token},
                      files = {'file':file}, verify=False)
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def getVialInfo(token, vialId):
    r = requests.get(f'{baseUrl}vialInfo/{vialId}',
            headers={'token':token}, verify=False)
    try:
        return r.content.decode()
    except:
        return r.content

def verifyVial(token, vialId):
    r = requests.get(f'{baseUrl}verifyVial/{vialId}',
            headers={'token':token}, verify=False)
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
                      headers = {'token':token}, verify=False)
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        res = r.content.decode()
        res = json.loads(res)
        return res, True

def uploadTaredVials(token, file):
    r = requests.post(f'{baseUrl}uploadTaredVials',
                     headers={'token': token},
                     files={'file':file}, verify=False)
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True


def getLocationsByStorage(token, storage):
    r = requests.get(f'{baseUrl}getLocationByStorage/{storage}',
                     headers={'token':token}, verify=False)
    try:
        res = r.content.decode()
        res = json.loads(res)
        return res
    except:
        return r.content


def getLists(token, listType):
    unCookedToken = json.loads(token.decode('utf-8'))
    username = unCookedToken['user']

    r = requests.get(f'{baseUrl}getLists/{listType}',
                     headers={'token':token}, verify=False)
    try:
        res = r.content.decode()
        res = json.loads(res)
        return res
    except:
        return r.content

def getEchoData(token, plateListId, sCtrlPlate, sDMSOplate):
    r = requests.get(f'{baseUrl}getEchoData/{plateListId}/{sCtrlPlate}/{sDMSOplate}',
            headers={'token':token}, verify=False)
    try:
        res = r.content.decode()
        res = json.loads(res)
        return res
    except:
        return r.content

def checkListName(token, listName):
    unCookedToken = json.loads(token.decode('utf-8'))
    username = unCookedToken['user']

    r = requests.get(f'{baseUrl}checkListName/{username}/{listName}',
                     headers={'token':token}, verify=False)
    try:
        res = r.content.decode()
        res = json.loads(res)
        retVal = res['msg']
        if retVal == 'Ok':
            return True
        else:
            return False
    except:
        return False


def saveListElements(token, accuElements, listId):
    unCookedToken = json.loads(token.decode('utf-8'))
    username = unCookedToken['user']

    r = requests.put(f'{baseUrl}saveListElements/{accuElements}/{listId}',
                     headers={'token':token}, verify=False)
    try:
        res = r.content.decode()
        res = json.loads(res)
        retVal = res['msg']
        if retVal != 'NotOk':
            return retVal
        else:
            return False
    except:
        return False

    
def createList(token, listName, listType):
    unCookedToken = json.loads(token.decode('utf-8'))
    username = unCookedToken['user']

    r = requests.put(f'{baseUrl}createList/{username}/{listName}/{listType}',
                     headers={'token':token}, verify=False)
    try:
        res = r.content.decode()
        res = json.loads(res)
        retVal = res['msg']
        if retVal != 'NotOk':
            return retVal
        else:
            return False
    except:
        return False


def deleteList(token, listId):
    unCookedToken = json.loads(token.decode('utf-8'))
    username = unCookedToken['user']

    r = requests.put(f'{baseUrl}deleteList/{username}/{listId}',
                     headers={'token':token}, verify=False)
    try:
        res = r.content.decode()
        res = json.loads(res)
        retVal = res['msg']
        if retVal == 'Ok':
            return True
        else:
            return False
    except:
        return False


def deleteListElements(token, listId):
    unCookedToken = json.loads(token.decode('utf-8'))
    username = unCookedToken['user']

    r = requests.put(f'{baseUrl}deleteListElements/{username}/{listId}',
                     headers={'token':token}, verify=False)
    try:
        res = r.content.decode()
        res = json.loads(res)
        retVal = res['msg']
        if retVal == 'Ok':
            return True
        else:
            return False
    except:
        return False

    
def searchLists(token, plateIdPk, batchIdPk):
    r = requests.get(f'{baseUrl}searchLists/{plateIdPk}/{batchIdPk}',
            headers={'token':token}, verify=False)
    try:
        data = ast.literal_eval(r.content.decode())
        return data
    except:
        print('Failed decode')
        return False


def getListById(token, batchIdPk):
    r = requests.get(f'{baseUrl}getListById/{batchIdPk}',
            headers={'token':token}, verify=False)
    try:
        data = ast.literal_eval(r.content.decode())
        return data
    except:
        print('Failed decode')
        return False


def getListInfoById(token, batchIdPk):
    r = requests.get(f'{baseUrl}getListInfoById/{batchIdPk}',
            headers={'token':token}, verify=False)
    try:
        data = ast.literal_eval(r.content.decode())
        return data
    except:
        print('Failed decode')
        return False


def validateBatch(token, batchIds, listType):
    r = requests.get(f'{baseUrl}validateBatches/{batchIds}/{listType}',
            headers={'token':token}, verify=False)
    try:
        data = ast.literal_eval(r.content.decode())
        return data
    except:
        print('Failed decode')
        return r.content

def saveBatchList(token, batchIds, listId):
    r = requests.get(f'{baseUrl}saveBatchList/{batchIds}/{listId}',
            headers={'token':token}, verify=False)
    try:
        data = ast.literal_eval(r.content.decode())
        return data
    except:
        print('Failed decode')
        return r.content

def getBatches(token, batchIds, vials, tubes, plates, present):
    r = requests.get(f'{baseUrl}searchBatches/{present}/{vials}/{tubes}/{plates}/{batchIds}',
            headers={'token':token}, verify=False)

    try:
        return r.content.decode()
    except:
        return r.content

def createEmptyVials(token, iNrVials):
    r = requests.put(f'{baseUrl}createEmptyVials/{iNrVials}',
            headers={'token':token}, verify=False)
    try:
        return r.content.decode()
    except:
        return r.content    
    
def getManyVials(token, vialIds):
    r = requests.get(f'{baseUrl}searchVials/{vialIds}',
            headers={'token':token}, verify=False)
    try:
        return r.content.decode()
    except:
        return r.content

def printBoxLabel(token, sBox):
    r = requests.get(f'{baseUrl}printBox/{sBox}',
                     headers={'token': token}, verify=False)
    res = r.content.decode()
    return res

def printVialLabel(token, sVial):
    r = requests.get(f'{baseUrl}printVial/{sVial}',
                     headers={'token': token}, verify=False)
    res = r.content.decode()
    return res

def printPlateLabel(token, sPlate):
    r = requests.get(f'{baseUrl}printPlate/{sPlate}',
                     headers={'token': token}, verify=False)
    res = r.content.decode()
    return res

def duplicatePlate(token, sPlate, sVolume):
    r = requests.get(f'{baseUrl}duplicatePlate/{sPlate}/{sVolume}',
                     headers={'token': token}, verify=False)
    res = r.content.decode()
    return res

def getFreePositions(token):
    r = requests.get(f'{baseUrl}getFreeBoxes',
                     headers={'token': token}, verify=False)
    res = r.content.decode()
    return res

def createMolImage(token, sId):
    r = requests.get(f'{baseUrl}createMolImage/{sId}',
                     headers={'token': token}, verify=False)
    res = r.content.decode()
    return res

def getMolImage(vialOrCompound):
    r = requests.get(f'{baseUrl}mols/{vialOrCompound}.png', verify=False)
    res = r.content
    return res

def getBox(token, box):
    r = requests.get(f'{baseUrl}getBox/{box}',
                     headers={'token': token}, verify=False)
    try:
        res = r.content.decode()
    except:
        res = r.content
    return res

def getBoxLocation(token, box):
    r = requests.get(f'{baseUrl}getBoxLocation/{box}',
                     headers={'token': token}, verify=False)
    try:
        res = r.content.decode()
    except:
        res = r.content
    return res

def getLocationPath(token, location):
    r = requests.get(f'{baseUrl}getLocationPath/{location}',
                     headers={'token': token}, verify=False)
    try:
        res = r.content.decode()
    except:
        res = r.content
    return res

def updateVialPosition(token, vial, box, pos):
    r = requests.put(f'{baseUrl}updateVialPosition/{vial}/{box}/{pos}',
                     headers={'token': token}, verify=False)
    if r.status_code != 200:
        return False
    else:
        return True

def transitVials(token, vials):
    r = requests.put(f'{baseUrl}transitVials/{vials}',
                      headers={'token': token}, verify=False)
    if r.status_code != 200:
        return False
    else:
        return True

def getLocationChildren(token, location):
    r = requests.get(f'{baseUrl}getLocationChildren/{location}',
                     headers={'token': token}, verify=False)
    try:
        res = r.content.decode()
    except:
        res = r.content
    return res

def moveBox(token, box, location):
    r = requests.put(f'{baseUrl}moveBox/{box}/{location}',
                     headers={'token': token}, verify=False)
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return None, True

def addBox(token, sParent, sBoxName, sBoxSize):
    r = requests.put(f'{baseUrl}addBox/{sParent}/{sBoxName}/{sBoxSize}',
                      headers={'token': token}, verify=False)
    if r.status_code != 200:
        return False
    else:
        return True

def updateBoxName(token, box, newName):
    r = requests.put(f'{baseUrl}updateBoxName/{box}/{newName}',
                     headers={'token': token}, verify=False)
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return None, True

def addLocation(token, sParent, sLocationName, sLocationType):
    r = requests.put(f'{baseUrl}addLocation/{sParent}/{sLocationName}/{sLocationType}',
                      headers={'token': token}, verify=False)
    if r.status_code != 200:
        return False
    else:
        return True

def deleteLocation(token, location):
    r = requests.put(f'{baseUrl}deleteLocation/{location}',
                      headers={'token': token}, verify=False)
    if r.status_code != 200:
        return r, False
    else:
        return r, True

def getMicroTubes(token, batches):
    r = requests.get(f'{baseUrl}getMicroTubes/{batches}',
                      headers={'token': token}, verify=False)
    try:
        res = r.content.decode()
    except:
        res = r.content
    return res


def getMicroTubesFromFile(token, file):
    r = requests.post(f'{baseUrl}getMicroTubesFromFile',
                     headers={'token': token},
                     files={'file':file}, verify=False)
    try:
        res = r.content.decode()
    except:
        res = r.content
    return res


def getRack(token, rack):
    r = requests.get(f'{baseUrl}getRack/{rack}',
                      headers={'token': token}, verify=False)
    try:
        res = r.content.decode()
    except:
        res = r.content

    if r.status_code != 200:
        return res, False
    else:
        return res, True

def printRack(token, rack):
    r = requests.get(f'{baseUrl}printRack/{rack}',
                      headers={'token': token}, verify=False)
    try:
        res = r.content.decode()
    except:
        res = r.content
    return res

def printRackList(token, rack):
    r = requests.get(f'{baseUrl}printRackList/{rack}',
                      headers={'token': token}, verify=False)
    try:
        res = r.content.decode()
    except:
        res = r.content
    return res

def createPlateFromRack(token, rack, volume):
    r = requests.get(f'{baseUrl}createPlateFromRack/{rack}/{volume}',
                      headers={'token': token}, verify=False)
    try:
        res = r.content.decode()
    except:
        res = r.content
    return res

def verifyLocation(token, location):
    r = requests.get(f'{baseUrl}verifyLocation/{location}',
                      headers={'token': token}, verify=False)
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def createRacks(token, nr_o_rs):
    r = requests.put(f'{baseUrl}createRacks/{nr_o_rs}',
                      headers={'token':token}, verify=False)
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True
    
def readScannedRack(token, location, file):
    r = requests.post(f'{baseUrl}readScannedRack',
                      headers={'token': token},
                      data={'location': location},
                      files={'file':file}, verify=False)
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def updateRackLocation(token, rack_id, box_id):
    r = requests.put(f'{baseUrl}updateRackLocation/{rack_id}/{box_id}',
                      headers={'token':token}, verify=False)
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def addMicrotube(token, tubeId, compBatch, volume, conc):
    r = requests.put(f'{baseUrl}addMicrotube/{tubeId}/{compBatch}/{volume}/{conc}',
                      headers={'token': token}, verify=False)
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def verifyPlate(token, plate):
    r = requests.get(f'{baseUrl}verifyPlate/{plate}',
                      headers={'token':token}, verify=False)
    if r.status_code != 200:
        return r.content.decode(), 0
    else:
        return r.content.decode(), 1


def createPlates(token, type, name, nr_o_ps, location, sDuplicate):
    r = requests.put(f'{baseUrl}createPlates/{type}/{name}/{nr_o_ps}/{location}/{sDuplicate}',
                      headers={'token':token}, verify=False)
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def createPlatesFromLabel(token, sStartPlate, type, name, nr_o_ps):
    r = requests.put(f'{baseUrl}createPlatesFromLabel/{sStartPlate}/{type}/{name}/{nr_o_ps}',
                      headers={'token':token}, verify=False)
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def getPlateForPlatemap(token, sPlate):
    r = requests.get(f'{baseUrl}getPlateForPlatemap/{sPlate}',
                     headers={'token':token}, verify=False)
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        res = r.content.decode()
        res = json.loads(res)

        return res, True


def getPlate(token, plate):
    r = requests.get(f'{baseUrl}getPlate/{plate}',
                      headers={'token': token}, verify=False)
    try:
        res = r.content.decode()
    except:
        res = r.content
    return res, r.status_code

def updatePlateName(token, plate, comment, location):
    r = requests.put(f'{baseUrl}updatePlateName/{plate}/{comment}/{location}',
                      headers={'token':token}, verify=False)
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
                      headers={'token':token}, verify=False)
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True


def uploadAccumulatedRows(token, accumulated_rows):
    json_data = json.dumps(accumulated_rows)

    r = requests.post(f'{baseUrl}uploadAccumulatedRows',
                      data = {'rows':json_data},
                      headers={'token':token}, verify=False)
    if r.status_code != 200:
        data = ast.literal_eval(r.content.decode())
        return data, False
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
                      headers={'token':token}, verify=False)
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def discardVial(token, vial_id):
    r = requests.put(f'{baseUrl}discardVial/{vial_id}',
                      headers={'token': token}, verify=False)
    if r.status_code != 200:
        return r, False
    else:
        return r, True

def discardPlate(token, plate_id):
    r = requests.put(f'{baseUrl}discardPlate/{plate_id}',
                      headers={'token': token}, verify=False)
    if r.status_code != 200:
        return r, False
    else:
        return r, True

def setPlateType(token, plate_id, plate_type):
    r = requests.put(f'{baseUrl}setPlateType/{plate_id}/{plate_type}',
                      headers={'token': token}, verify=False)
    if r.status_code != 200:
        return r, False
    else:
        return r, True

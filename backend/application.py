import tornado.gen
import json
import logging
import ast
import datetime
import time
import os, random, string
import re
import util
import codecs
from auth import jwtauth
from rdkit import Chem
from rdkit.Chem import Draw
import mydb
import config
import pandas as pd
from os.path import exists

db = mydb.disconnectSafeConnect()
cur = db.cursor()
NR_OF_VIALS_IN_BOX = 200

def res_to_json(response, cursor):
    columns = cursor.description()
    to_js = [{columns[index][0]:column for index,
              column in enumerate(value)} for value in response]
    return to_js

def createPngFromMolfile(regno, molfile):
    m = Chem.MolFromMolBlock(molfile)
    try:
        Draw.MolToFile(m, f'mols/{regno}.png', size=(300, 300))
    except:
        logging.error(f"regno {regno} is nostruct")


class home(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        self.redirect('/vialdb/index.html')
        return

def getNewLocId():
    sSql = f"select pkey from loctree.location_id_sequence"
    cur.execute(sSql)
    pkey = cur.fetchall()[0][0] +1
    sSql = f"update loctree.location_id_sequence set pkey={pkey}"
    cur.execute(sSql)
    return 'SL' + str(pkey)

def getNewPlateId():
    def nextPossiblePlate():
        sSql = f"select pkey from cool.plate_sequence"
        cur.execute(sSql)
        pkey = cur.fetchall()[0][0] +1
        sSql = f"update cool.plate_sequence set pkey={pkey}"
        cur.execute(sSql)
        return pkey

    sPlate = ''
    pkey = 0
    while(True):
        pkey = nextPossiblePlate()
        sPlate = 'P' + str(pkey)
        sSql = f"select plate_id from cool.plate where plate_id = '{sPlate}'"
        cur.execute(sSql)
        res = cur.fetchall()
        if len(res) > 0:
            pass
        else:
            break

    return sPlate


def getNewRackId():
    def nextPossibleRack():
        sSql = f"select pkey from microtube.matrix_sequence"
        cur.execute(sSql)
        pkey = cur.fetchall()[0][0] +1
        sSql = f"update microtube.matrix_sequence set pkey={pkey}"
        cur.execute(sSql)
        return pkey

    sPlate = ''
    pkey = 0
    while(True):
        pkey = nextPossibleRack()
        sRack = 'MX' + str(pkey).zfill(4)
        sSql = f"select matrix_id from microtube.matrix where matrix_id = '{sRack}'"
        cur.execute(sSql)
        res = cur.fetchall()
        if len(res) > 0:
            pass
        else:
            break

    return sRack


class PingDB(tornado.web.RequestHandler):
    def get(self):
        sSql = "SELECT * FROM glass.box_sequence"
        cur.execute(sSql)


@jwtauth
class AddMicrotube(tornado.web.RequestHandler):
    def put(self, sTubeId, sBatchId, sVolume, sConc):
        volume = -1
        try:
            conc = float(sConc)/1000
        except:
            sError = f"conc is not a number {sConc}"
            logging.error(sError)
            self.set_status(400)
            self.finish(sError)
            return
        try:
            if sVolume == '' or float(sVolume):
                if sVolume == '':
                    volume = -1
                else:
                    volume = float(sVolume)/1000000
        except:
            sError = f"volume is not a number {sVolume}"
            logging.error(sError)
            self.set_status(400)
            self.finish(sError)
            return
        try:
            #0019953454 microtube_id is 10 digits
            ss = re.search(r'^(\d){10}$', sTubeId).group(0)
        except:
            sError = f"error not valid microtube id {sTubeId}"
            logging.error(sError)
            self.set_status(400)
            self.finish(sError)
            return
        sSql = f"""insert into microtube.tube
        (tube_id, notebook_ref, volume, conc, tdate, created_date)
        values
        ('{sTubeId}', '{sBatchId}', {volume}, {conc}, now(), now())
        """
        try:
            cur.execute(sSql)
        except Exception as e:
            sError = str(e)
            #logging.error(sError)
            self.set_status(400)
            self.finish(sError)
            return


@jwtauth
class getMicroTubes(tornado.web.RequestHandler):
    def get(self, sBatches):
        if len(sBatches) < 1:
            logging.error("no batch")
            self.write(json.dumps({}))
            return
        saBatches = sBatches.split()
        saBatches = list(set(saBatches))
        logging.info(saBatches)
        jResTot = list()

        def makeJson(tData, jRes, sId):
            if len(tData) == 0:
                return jRes
            for row in tData:
                try:
                    jRes.append({"batchId":row[0],
                                 "tubeId":row[1],
                                 "volume": row[2],
                                 "matrixId": row[3],
                                 "position": str(row[4]),
                                 "location": str(row[5])
                    })
                except:
                    logging.error('Failed at appending ' + sId)
                return jRes

        jRes = list()
        for sId in saBatches:
            sSql = """select
                      t.notebook_ref as batchId, t.tube_id as tubeId,
                      t.volume*1000000 as volume, m.matrix_id as matrixId,
                      mt.position as position, m.location as location
                      from microtube.tube t,
                           microtube.v_matrix_tube mt,
                           microtube.v_matrix m
                      where
                      t.tube_id = mt.tube_id and
                      m.matrix_id = mt.matrix_id and
                      t.notebook_ref = '%s'
               """ % sId
            try:
                sSlask = cur.execute(sSql)
                tRes = cur.fetchall()
            except Exception as e:
                logging.error("Error: " + str(e) + ' problem with batch:' + sId)
                return
            if len(tRes) == 0:
                sSql = f"""select
                t.notebook_ref as batchId, t.tube_id as tubeId,
                t.volume*1000000 as volume, m.matrix_id as matrixId,
                mt.position as position, m.location as location
                from microtube.tube t,
                microtube.v_matrix_tube mt,
                microtube.v_matrix m
                where
                t.tube_id = mt.tube_id and
                m.matrix_id = mt.matrix_id and
                t.tube_id = '{sId}'
                """
                try:
                    sSlask = cur.execute(sSql)
                    tRes = cur.fetchall()
                except Exception as e:
                    logging.error("Error: " + str(e) + ' problem with batch:' + sId)
                    return

            jRes = makeJson(tRes, jRes, sId)
        self.write(json.dumps(jRes, indent=4))


@jwtauth
class CreateRacks(tornado.web.RequestHandler):
    def put(self, sNumberOfRacks):
        saNewRacks = []
        #rackKeys = []
        #rackValues = []
        iNumberOfRacks = int(sNumberOfRacks)
        for i in range(iNumberOfRacks):
            sNewRack = getNewRackId()
            sSql = f"""
            insert into microtube.matrix
            (matrix_id, created_date)
            values
            ('{sNewRack}', now())
            """
            cur.execute(sSql)
            saNewRacks.append(sNewRack)
            doPrintRack(sNewRack)

        res = json.dumps(saNewRacks, indent = 4)
        self.write(res)


@jwtauth
class CreatePlatesFromLabel(tornado.web.RequestHandler):
    
    def put(self, sStartPlate, sPlateType, sPlateName, sNumberOfPlates):

        def checkIfPlatesAreFree(iStart, iNumberOfPlates):
            lRetVal = True
            for i in range(iStart,iStart + iNumberOfPlates):
                sSql = f'''
                select plate_id from cool.plate where plate_id = 'p{str(i).zfill(6)}'
                '''
                sSlask = cur.execute(sSql)
                tRes = cur.fetchall()
                if len(tRes) > 0:
                    lRetVal = False
                    break
            return lRetVal

        
        saNewPlates = dict()
        plateKeys = []
        plateValues = []
        iNumberOfPlates = int(sNumberOfPlates)

        pattern = '([0-9]{6})$'
        m = re.search(pattern, sStartPlate)
        if m:
            iStart = int(m.groups()[0])
        else:
            sError = f'Error in plate format {sStartPlate}'
            self.set_status(400)
            self.finish(sError)
            logging.error(sError)
            return

        if checkIfPlatesAreFree(iStart, iNumberOfPlates):
            pass
        else:
            sError = f'Error plate already registered'
            self.set_status(400)
            self.finish(sError)
            logging.error(sError)
            return

        if sPlateType == "96":
            # This is the type_id in the db for 96 well plates
            iPlateType = 1
        elif sPlateType == "384":
            # This is the type_id in the db for 384 well plates
            iPlateType = 16
        elif sPlateType == "1536":
            # This is the type_id in the db for 1536 well plates
            iPlateType = 47
        for i in range(iNumberOfPlates):
            ii = str(i + 1)
            iii = ii.zfill(3)
            sNewplateName = f"{iii}: {sPlateName}"
            sPlateId = f"P{str(iStart + i).zfill(6)}"
            sSql = f"""
            insert into cool.plate (plate_id,
            config_id,
            type_id,
            comments,
            created_date,
            updated_date)
            values (
            '{sPlateId}',
            '{sPlateId}',
            {iPlateType},
            '{sNewplateName}',
            now(),
            now())"""
            cur.execute(sSql)
            plateKeys.append(sPlateId)
            #doPrintPlate(sPlateId)
            plateValues.append(sNewplateName)
        for i in range(len(plateKeys)):
            saNewPlates[plateKeys[i]] = plateValues[i]
        res = json.dumps(saNewPlates, indent = 4)
        self.write(res)



@jwtauth
class CreatePlates(tornado.web.RequestHandler):
    def put(self, sPlateType, sPlateName, sNumberOfPlates):
        saNewPlates = dict()
        plateKeys = []
        plateValues = []
        iNumberOfPlates = int(sNumberOfPlates)
        if sPlateType == "96":
            # This is the type_id in the db for 96 well plates
            iPlateType = 1
        elif sPlateType == "384":
            # This is the type_id in the db for 384 well plates
            iPlateType = 16
        elif sPlateType == "1536":
            # This is the type_id in the db for 1536 well plates
            iPlateType = 47
        for i in range(iNumberOfPlates):
            ii = str(i + 1)
            iii = ii.zfill(3)
            sNewplateName = f"{iii}: {sPlateName}"
            sPlateId = getNewPlateId()
            sSql = f"""
            insert into cool.plate (plate_id,
            config_id,
            type_id,
            comments,
            created_date,
            updated_date)
            values (
            '{sPlateId}',
            '{sPlateId}',
            {iPlateType},
            '{sNewplateName}',
            now(),
            now())"""
            cur.execute(sSql)
            plateKeys.append(sPlateId)
            doPrintPlate(sPlateId)
            plateValues.append(sNewplateName)
        for i in range(len(plateKeys)):
            saNewPlates[plateKeys[i]] = plateValues[i]
        res = json.dumps(saNewPlates, indent = 4)
        self.write(res)


@jwtauth
class UpdatePlateName(tornado.web.RequestHandler):
    def put(self, sPlate, sPlateName):
        sSql = f"""
        update cool.plate set comments = '{sPlateName}'
        where plate_id = '{sPlate}'
        """
        cur.execute(sSql)


@jwtauth
class MergePlates(tornado.web.RequestHandler):
    def post(self):

        def getQuadrant(quadrant):
            sSql = f"""
            select quadrant, well96, well384
            from cool.map96to384
            where quadrant = {quadrant}
            order by well96
            """
            cur.execute(sSql)
            df = pd.DataFrame(cur.fetchall())
            return df

        def getPlate(sPlate):
            if sPlate.startswith('P'):
                sSql = f"""
                SELECT
                p.plate_id,
                c.well,
                compound_id,
                notebook_ref,
                c.form,
                c.conc,
                c.volume
                FROM cool.config c, cool.plate p, cool.plating_sequence ps
                WHERE p.CONFIG_ID = c.CONFIG_ID
                and p.TYPE_ID = ps.TYPE_ID
                and c.WELL = ps.WELL and p.plate_id = '{sPlate}'
	        order by ps.seq"""
            elif sPlate.startswith('MX'):
                sSql = f"""
                select
                mt.matrix_id plate,
                mt.position well,
                b.compound_id,
                t.notebook_ref,
                'DMSO' form,
                t.conc,
                t.VOLUME
                from microtube.tube t, microtube.matrix_tube mt, bcpvs.batch b
                where t.tube_id = mt.tube_id
                and b.notebook_ref = t.notebook_ref
                and mt.matrix_id = '{sPlate}'
                """

            sSlask = cur.execute(sSql)
            tRes = cur.fetchall()
            return tRes
        
        def transferWells(quadrant, sourcePlate, targetPlate):
            for i in sourcePlate:
                sPlate = i[0]
                sWell = i[1]
                sCmpId = i[2]
                sBatch = i[3]
                sForm = i[4]
                sConc = i[5]
                if sConc == None:
                    sConc = 'NULL'
                dfTargetWell = quadrant.loc[quadrant[1] == sWell][2]
                sTargetWell = list(dfTargetWell)[0]
                sSql = f"""
                insert into cool.config
                (config_id, well, compound_id, notebook_ref, form, conc, volume)
                values
                (
                '{targetPlate}',
                '{sTargetWell}',
                '{sCmpId}',
                '{sBatch}',
                '{sForm}',
                {sConc},
                '{sVolume}'
                )
                """
                cur.execute(sSql)
        
        sVolume = self.get_argument("volume")
        q1 = self.get_argument("q1").upper()
        q2 = self.get_argument("q2").upper()
        q3 = self.get_argument("q3").upper()
        q4 = self.get_argument("q4").upper()
        targetPlate = self.get_argument("target").upper()

        sSql = f"""
        select count(c.config_id) from cool.plate p, cool.config c
        where p.config_id = c.config_id
        and p.plate_id = '{targetPlate}'
        """
        sSlask = cur.execute(sSql)
        tRes = cur.fetchall()
        if tRes[0][0] > 0:
            sError = 'Target plate not empty'
            self.set_status(400)
            self.finish(sError)
            return
        
        if q1 != "":
            quadrant = getQuadrant(1)
            plate = getPlate(q1)
            transferWells(quadrant, plate, targetPlate)
        if q2 != "":
            quadrant = getQuadrant(2)
            plate = getPlate(q2)
            transferWells(quadrant, plate, targetPlate)
        if q3 != "":
            quadrant = getQuadrant(3)
            plate = getPlate(q3)
            transferWells(quadrant, plate, targetPlate)
        if q4 != "":
            quadrant = getQuadrant(4)
            plate = getPlate(q4)
            transferWells(quadrant, plate, targetPlate)

@jwtauth
class SetPlateType(tornado.web.RequestHandler):
    def put(self, sPlate, sPlateType):
        if sPlateType == "96":
            # This is the type_id in the db for 96 well plates
            iPlateType = 1
        elif sPlateType == "384":
            # This is the type_id in the db for 384 well plates
            iPlateType = 16
        elif sPlateType == "1536":
            # This is the type_id in the db for 1536 well plates
            iPlateType = 47
        else:
            sError = 'Wrong plate size'
            logging.error(f'Wrong plate size {sPlateType}')
            self.set_status(400)
            self.finish(sError)
            return

        sSql = f"""select plate_id, type_id from cool.plate where plate_id = '{sPlate}'"""
        cur.execute(sSql)
        tRes = cur.fetchall()
        if len(tRes) == 0:
            sError = 'Plate not found'
            logging.error(f'{sError} {sPlate}')
            self.set_status(400)
            self.finish(sError)
            return

        sSql = f'''
        update cool.plate
        set type_id = '{iPlateType}'
        where plate_id = '{sPlate}'
        '''
        self.finish()

    
@jwtauth
class UploadWellInformation(tornado.web.RequestHandler):
    def post(self):
        sPlate = self.get_argument("plate_id")
        sWell = self.get_argument("well")
        sCompound = self.get_argument("compound_id")
        sBatch = self.get_argument("batch")
        sForm = self.get_argument("form")
        sConc = self.get_argument("conc")
        sVolume = self.get_argument("volume")

        sSql = f'''insert into cool.config
        (config_id, well, compound_id, notebook_ref, form, conc, volume)
        values
        ('{sPlate}', '{sWell}', '{sCompound}', '{sBatch}', '{sForm}', '{sConc}', '{sVolume}')
        '''
        try:
            cur.execute(sSql)
        except Exception as e:
            self.set_status(400)
            self.finish(str(e))


@jwtauth
class VerifyPlate(tornado.web.RequestHandler):
    def get(self, sPlate):
        if re.match("^[pP]{1}[0-9]{6}$", sPlate):
            sSql = f"""
            select wells from cool.plate, cool.plate_type
            where plate.type_id = plate_type.type_id
            and plate.plate_id ='{sPlate}'
            """
        elif re.match("^[mM][xX]{1}[0-9]{4}$", sPlate):
            sSql = f"""select 96 wells from microtube.matrix
            where matrix_id = '{sPlate}'
            """
        else:
            sError = 'Plate not found'
            self.set_status(400)
            self.finish(sError)
            return

        cur.execute(sSql)
        tRes = cur.fetchall()
        if len(tRes) == 0:
            sError = 'Plate not found'
            self.set_status(400)
            self.finish(sError)
            return
        self.finish(json.dumps(res_to_json(tRes, cur), indent=4))


@jwtauth
class GetPlate(tornado.web.RequestHandler):
    def get(self, sPlate):
        sSql = f"""select plate_id from cool.plate
        where plate_id = '{sPlate}'
        """
        sSlask = cur.execute(sSql)
        tRes = cur.fetchall()
        if len(tRes) == 0:
            sError = 'Plate not found'
            self.set_status(400)
            self.finish(sError)
            logging.error(sError)
            return

        sSql = f"""
        SELECT p.comments description,
        p.plate_id,
        c.well,
        compound_id,
        notebook_ref,
        c.form,
        c.conc,
        c.volume,
        p.TYPE_ID
        FROM cool.config c, cool.plate p, cool.plating_sequence ps
        WHERE p.CONFIG_ID = c.CONFIG_ID
        and p.TYPE_ID = ps.TYPE_ID
        and c.WELL = ps.WELL and p.plate_id = '{sPlate}'
	order by ps.seq"""
        sSlask = cur.execute(sSql)
        tRes = cur.fetchall()
        self.write(json.dumps(res_to_json(tRes, cur), indent=4))


@jwtauth
class UpdateRackLocation(tornado.web.RequestHandler):
    def put(self, sRack, sLocation):
        sSql = f"""
        update microtube.matrix set location = '{sLocation}'
        where matrix_id = '{sRack}'
        """
        try:
            sSlask = cur.execute(sSql)
            self.finish()
        except Exception as e:
            self.set_status(400)
            self.finish(str(e))
            

@jwtauth
class MoveBox(tornado.web.RequestHandler):
    def put(self, sBox, sLocation):
        sSql = f"""
        update loctree.locations set parent = '{sLocation}'
        where loc_id = '{sBox}'
        """
        try:
            sSlask = cur.execute(sSql)
            self.finish()
        except Exception as e:
            self.set_status(400)
            self.finish(str(e))
            

@jwtauth
class ReadScannedRack(tornado.web.RequestHandler):
    def post(self):
        try:
            sLocation = self.get_argument("location")
            file1 = self.request.files['file'][0]
            sFile = tornado.escape.xhtml_unescape(file1.body)
        except:
            logging.error("Error cant find file1 in the argument list")
            return

        m = re.search("Rack Base Name: (\w\w\d+)", str(file1['body']))
        if m:
            sRackId = m.groups()[0]
        else:
            logging.error("Error cant find rack-id in file")
            return

        original_fname = file1['filename']
        extension = os.path.splitext(original_fname)[1]
        fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
        finalFilename = "uploads/" + original_fname
        output_file = open("uploads/" + original_fname, 'w')
        output_file.write(sFile)
        output_file.close()

        fNewFile = open(finalFilename, mode='rU')
        saFile = fNewFile.readlines()
        iOk = 0
        iError = 0
        saError = []
        for sLine in saFile:
            m = re.search("\s+(\w\d\d);\s+(\d+)", sLine)
            if m:
                sPosition = m.groups()[0]
                sTube = m.groups()[1]
            else:
                continue
            sSql = """select matrix_id from microtube.matrix_tube
            where tube_id = '%s'
            """ % sTube
            sSlask = cur.execute(sSql)
            tRes = cur.fetchall()

            if len(tRes) < 1:
                sSql = f'''insert into microtube.matrix_tube
                (position, matrix_id, tube_id)
                values
                ('{sPosition}', '{sRackId}', '{sTube}')
                '''
                try:
                    sSlask = cur.execute(sSql)
                except Exception as e:
                    iError += 1
                    iOk -= 1
                    saError.append(sTube)
                    err = str(e)
            else:
                sSql = """update microtube.matrix_tube set position = '%s', matrix_id = '%s'
                where tube_id = '%s'
                """ % (sPosition, sRackId, sTube)
                try:
                    sSlask = cur.execute(sSql)
                except Exception as e:
                    iError += 1
                    iOk -= 1
                    saError.append(sTube)
                    err = str(e)
                    logging.error(f'Failed updating tube {sTube} {err}')
            iOk += 1

        sSql = f"""
        update microtube.matrix set location = '{sLocation}'
        where matrix_id = '{sRackId}'
        """
        slask = cur.execute(sSql)
        self.finish(json.dumps({'FailedTubes': saError,
                                'iOk': iOk,
                                'iError': iError,
                                'sRack': sRackId
        }))


@jwtauth
class getRack(tornado.web.RequestHandler):
    def get(self, sRacks):
        logging.info(sRacks)
        jResTot = list()

        def makeJson(tData, jRes, sId):
            if len(tData) == 0:
                return jRes
            iRow = 0
            for row in tData:
                try:
                    if iRow < 10:
                        sRow = '0' + str(iRow)
                    else:
                        sRow = str(iRow)
                    jRes.append({"batchId":row[0],
                                 "tubeId":row[1],
                                 "volume": row[2],
                                 "matrixId": row[3],
                                 "position": str(row[4]),
                                 "location": str(row[5]),
                                 "conc": row[6],
                                 "compoundId": row[7],
                                 "locId": row[9],
                                 "iRow" : sRow
                    })
                    iRow += 1
                except Exception as e:
                    logging.error('Failed at appending ' + sId + ' ' + str(e))
            return jRes

        jRes = list()
        saRacks = set(sRacks.split())
        for sRack in saRacks:
            sSql = f"""select
            t.notebook_ref as batchId, t.tube_id as tubeId, t.volume*1000000 as volume,
            m.matrix_id as matrixId, mt.position as position, m.location as location,
            t.conc * 1000, compound_id, SUBSTR(mt.position, 2,3) as rackrow, m.loc_id
            from microtube.tube t, microtube.v_matrix_tube mt, microtube.v_matrix m,
            bcpvs.batch b
            where
            t.notebook_ref = b.notebook_ref and
            t.tube_id = mt.tube_id and
            m.matrix_id = mt.matrix_id and
            mt.matrix_id = '{sRack}' order by rackrow, position"""
            try:
                sSlask = cur.execute(sSql)
                tRes = cur.fetchall()
            except Exception as e:
                logging.error("Error: " + str(e) + ' problem with rack:' + sRack)
                return
            jRes = makeJson(tRes, jRes, sRack)
        self.write(json.dumps(jRes, indent=4))


@jwtauth
class UploadBinary(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        os_name = self.get_argument("os_name")

        try:
            # self.request.files['file'][0]:
            # {'body': 'Label Automator ___', 'content_type': u'text/plain', 'filename': u'k.txt'}
            file1 = self.request.files['file'][0]
        except:
            logging.error("Error cant find file1 in the argument list")
            return

        bin_file = ""
        if os_name == 'Windows':
            bin_file = f'dist/{os_name}/ce.exe'
        elif os_name == 'Linux':
            bin_file = f'dist/{os_name}/ce'
        elif os_name == 'Darwin':
            bin_file = f'dist/{os_name}/ce'
        else:
            # unsupported OS
            self.set_status(500)
            self.write({'message': 'OS not supported'})
            return
        
        output_file = open(bin_file, 'wb')
        output_file.write(file1['body'])
        output_file.close()

@jwtauth
class UploadVersionNo(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        ver_no = self.get_argument("ver_no")
        ver_file = "ver.dat"

        with open(ver_file, "r") as f:
            data = json.load(f)
        
        data["version"] = ver_no

        with open(ver_file, "w") as f:
            json.dump(data, f)

@jwtauth
class UploadLauncher(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        os_name = self.get_argument("os_name")

        try:
            # self.request.files['file'][0]:
            # {'body': 'Label Automator ___', 'content_type': u'text/plain', 'filename': u'k.txt'}
            file1 = self.request.files['file'][0]
        except:
            logging.error("Error cant find file1 in the argument list")
            return

        bin_file = ""
        if os_name == 'Windows':
            bin_file = f'dist/launchers/{os_name}/cello.exe'
        elif os_name == 'Linux':
            bin_file = f'dist/launchers/{os_name}/cello'
        elif os_name == 'Darwin':
            bin_file = f'dist/launchers/{os_name}/cello'
        else:
            # unsupported OS
            self.set_status(500)
            self.write({'message': 'OS not supported'})
            return
        
        output_file = open(bin_file, 'wb')
        output_file.write(file1['body'])
        output_file.close()
            
@jwtauth
class UploadTaredVials(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        try:
            # self.request.files['file'][0]:
            # {'body': 'Label Automator ___', 'content_type': u'text/plain', 'filename': u'k.txt'}
            file1 = self.request.files['file'][0]
        except:
            logging.error("Error cant find file1 in the argument list")
            return
        original_fname = file1['filename']
        extension = os.path.splitext(original_fname)[1]
        fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
        finalFilename = "uploads/" + original_fname
        output_file = open("uploads/" + original_fname, 'wb')
        output_file.write(file1['body'])
        output_file.close()

        fNewFile = open(finalFilename, mode='rU')
        saFile = fNewFile.readlines()
        iOk = 0
        iError = 0
        saError = []
        for sLine in saFile:
            saLine = sLine.split('\t')
            if len(saLine) == 1:
                saLine = sLine.split(',')

            if len(saLine) == 4 or len(saLine) == 2:
                sVial = ''.join(saLine[0].split())
                m = re.search(r'V\d\d\d\d\d(\d|\d\d)', sVial)
                if m:
                    sTare = ''.join(saLine[1].split())
                    try:
                        sSql = f"""insert into glass.vial (vial_id, type_id, tare, updated_date) 
                                   values ('{sVial}', 2, {sTare}, now())"""
                        sSlask = cur.execute(sSql)
                        iOk += 1
                    except Exception as e:
                        res = str(e).find('1062') # Duplicate key error is 1062 and it is ok
                        if res == 1:
                            sSql = f"""update glass.vial set
                            tare = {sTare},
                            updated_date = now()
                            where vial_id = '{sVial}'
                            """
                            sSlask = cur.execute(sSql)
                            logging.info("Upload vial: " + sVial + ' Tare: ' + sTare)
                            iOk += 1
                        else:
                            logging.error(str(e))
                            saError.append(sVial)
                            iError += 1

        self.finish(json.dumps({'FailedVials':saError, 'iOk':iOk, 'iError':iError}))

def logVialChange(sVialId, sLogMessage, sNewPos=None):
    sSql = f"""
    insert into glass.vial_log (vial_id, updated_date, changes)
    values ('{sVialId}', now(), '{sLogMessage}')
    """
    try:
        sSlask = cur.execute(sSql)
    except Exception as e:
        logging.error("Vial_log error {str(e)}")

def getVialPosition(sVialId):
    sSql = f"""select IFNULL(v.location, '') location, l.name, IFNULL(v.pos, '') coordinate
               from glass.vial v
               left join loctree.locations l on v.location = l.loc_id
               where v.vial_id='{sVialId}'"""
    
    sSlask = cur.execute(sSql)
    tRes = cur.fetchall()
    logging.info(tRes)
    if len(tRes) == 0:
        return '', '', ''
    return str(tRes[0][0]).upper(), str(tRes[0][1]), tRes[0][2]

def getBoxFromDb(sBox):
    positions = 0
    sSql = f"""select subpos from loctree.locations, loctree.location_type
    where loctree.locations.loc_id = '{sBox}'
    and loctree.locations.type_id = loctree.location_type.type_id"""
    sSlask = cur.execute(sSql)
    tRes = cur.fetchall()
    if len(tRes) != 1:
        return

    try:
        positions = int(tRes[0][0])
    except:
        pass

    sSlask = cur.execute(f"""select a.coordinate, tt.vial_id,
 tt.compound_id, tt.notebook_ref batch_id
 from
 (SELECT v.pos, v.vial_id, c.compound_id, v.location, v.notebook_ref
 from glass.vial v
 left join bcpvs.batch c on v.notebook_ref = c.notebook_ref
 where v.location = '{sBox}') tt
 right outer join
 (select coordinate from glass.box_sequence order by coordinate limit {positions}) a
 on tt.pos = a.coordinate
 order by a.coordinate asc""")
    
    tRes = cur.fetchall()

    #jRes = []
    #for row in tRes:
    #    jRes.append({"vialId":row.vial_id,
    #                 "coordinate":row.coordinate,
    #                 "batchId":row.batch_id,
    #                 "compoundId":row.compound_id,
    #                 "boxId":row.box_id,
    #                 "boxDescription":row.box_description})
    return res_to_json(tRes, cur)#jRes

def doPrint(sCmp, sBatch, sType, sDate, sVial):

    zplVial = """^XA
^MMT
^PW400
^LL0064
^LS210
^CFA,20
^A0,25,20
^FO300,20^FDCmp: %s^FS
^A0,25,20
^FO300,45^FDBatch: %s^FS
^A0,25,20
^FO300,70^FDConc: %s^FS
^A0,25,20
^FO300,95^FDDate: %s^FS
^A0,25,20
^FO300,120^FDVial: %s^FS

^FX Third section with barcode.
^BY2,3,45
^FO300,142^BCN^FD%s^FS
^XZ
""" % (sCmp, sBatch, sType, sDate, sVial, sVial)


    f = open('/tmp/file.txt','w')
    f.write(zplVial)
    f.close()
    os.system("lp -h homer.scilifelab.se:631 -d CBCS-GK420t /tmp/file.txt")


@jwtauth
class verifyVial(tornado.web.RequestHandler):
    def get(self, sVial):
        sSql = f"""SELECT notebook_ref batch_id, type_id vial_type
                  from glass.vial
                  where vial_id='{sVial}'"""
        tRes = cur.execute(sSql)
        tRes = cur.fetchall()
        lError = False
        if len(tRes) != 1:
            lError = True
            sError = 'Vial not found ' + str(sVial)
            logging.error(sError)
            logging.error(tRes)
            #elif tRes[0]['vial_type'] not in (None, '', 0):
        elif len(str(tRes[0][0])) > 4:
            #lError = True
            sError = 'Vial already checked in ' + sVial
      
        if lError:
            self.set_status(400)
            self.finish(sError)
            logging.error(sError)
            logging.error(tRes)
            return

        sSql = f"""
        select v.vial_id, v.notebook_ref batch_id, b.compound_id,
        IFNULL(v.tare, '') tare,
        b.BIOLOGICAL_MW batch_formula_weight,
        IFNULL(v.net, '') net,
        IFNULL(v.gross, '') gross,
        FORMAT(FLOOR(v.conc), 0) conc,
        IFNULL(ROUND((((v.net*1000)/b.BIOLOGICAL_MW)/conc)*1000000), '') dilution_factor
        from glass.vial v, bcpvs.batch b
        where v.notebook_ref = b.notebook_ref and v.vial_id = '{sVial}'
        """
        sSlask = cur.execute(sSql)
        tRes = cur.fetchall()
        if len(tRes) == 0:
            tRes = [{'vial_id': sVial,
                     'batch_id': '',
                     'compound_id': '',
                     'tare': '',
                     'batch_formula_weight': '',
                     'net': '',
                     'gross': '',
                     'conc': '',
                     'dilution_factor':''}]
            self.write(json.dumps(tRes))
            return
        self.write(json.dumps(res_to_json(tRes, cur)))


@jwtauth
class batchInfo(tornado.web.RequestHandler):
    def get(self, sBatch):
        sSlask = cur.execute("""SELECT b.batch_id,
                           b.compound_id, batch_formula_weight
                           from ddd.batch b
                           where b.batch_id = '%s'
                           """ % (sBatch))
        tRes = cur.fetchall()
        if len(tRes) != 1:
            lError = True
            sError = 'Batch not found ' + str(sBatch)
            logging.error(sError)
            self.set_status(400)
            self.finish(sError)
            return
        self.write(json.dumps(res_to_json(tRes, cur)))


@jwtauth
class EditVial(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        sVial = self.get_argument("sVial")
        sBatch = self.get_argument("batch_id")
        conc = self.get_argument("conc")
        sTare = self.get_argument("tare")
        sGross = self.get_argument("iGross")
        sNetWeight = self.get_argument("iNetWeight")

        if sTare in ('', 'None'):
            sTare = 'NULL'
        if sNetWeight in ('', 'None'):
            sNetWeight = 'NULL'
        if sGross in ('', 'None'):
            sGross = 'NULL'
        
        sSql = f"""
        select notebook_ref from glass.vial
        where vial_id = '{sVial}'"""
        cur.execute(sSql)
        tRes = cur.fetchall()
        if len(tRes) == 1 and tRes[0][0] == None:
            pass
        elif len(tRes) > 0 and tRes[0][0] != sBatch:
            sError = f"{sVial} already assigned to batch {tRes[0][0]}"
            logging.error("Error updating vial " + str(sVial))
            logging.error(sError)
            self.set_status(400)
            self.finish(sError)
            return

        logging.info(self.request.arguments.values())
        if conc in ('', 'Solid'):
            sSql = f"""
            update glass.vial set
            notebook_ref = '{sBatch}',
            conc = NULL,
            form = 'solid',
            updated_date = now(),
            tare = {sTare},
            net = {sNetWeight},
            gross = {sGross}
            where vial_id = '{sVial}'
            """
        else:
            sSql = f"""
            update glass.vial set
            notebook_ref = '{sBatch}',
            conc = '{conc}',
            form = NULL,
            updated_date = now(),
            tare = {sTare},
            net = {sNetWeight},
            gross = {sGross}
            where vial_id = '{sVial}'
            """

        try:
            cur.execute(sSql)
        except Exception as e:
            sError = str(e)
            logging.error("Error updating vial " + str(sVial))
            logging.error("Error: " + sError)
            self.set_status(400)
            self.finish(sError)
            return
        logging.info("Done editing vial: " + str(sVial))

        sSql = f"""
        select
        ROUND((((v.net*1000)/b.BIOLOGICAL_MW)/conc)*1000000) dilution_factor
        from glass.vial v, bcpvs.batch b
        where v.notebook_ref = b.notebook_ref and v.vial_id = '{sVial}'
        """
        sSlask = cur.execute(sSql)
        tRes = cur.fetchall()
        self.finish(json.dumps(res_to_json(tRes, cur)))


def doPrintPlate(sPlate):
    s = f'''
^XA
^MMT
^PW400
^LL0064
^LS0
^BY2,3,43^FT20,48^BCN,,Y,N
^FD>:P>{sPlate}^FS
^FT270,48^A0N,28,31^FH\^FD{sPlate}^FS
^PQ1,0,1,Y^XZ
'''
    f = open('/tmp/file.txt','w')
    f.write(s)
    f.close()
    os.system("lp -h homer.scilifelab.se:631 -d CBCS-GK420t_plates  /tmp/file.txt")


def doPrintRack(sRack):
    m = re.search("(\d\d\d\d)", sRack)
    if m:
        sNumbers = m.groups()[0]
    else:
        return
    
    s = f'''^XA
^MMT
^PW400
^LL0064
^LS0
^BY2,3,43^FT20,48^BCN,,Y,N
^FD>:MX>5{sNumbers}^FS
^FT270,48^A0N,28,31^FH\^FD{sRack}^FS
^PQ1,0,1,Y^XZ
'''
    f = open('/tmp/file.txt','w')
    f.write(s)
    f.close()
    os.system("lp -h homer.scilifelab.se:631 -d CBCS-GK420t_plates /tmp/file.txt")
    
        
@jwtauth
class PrintRack(tornado.web.RequestHandler):
    def get(self, sRack):
        logging.info("Printing label for rack " + sRack)
        doPrintRack(sRack)


@jwtauth
class printVial(tornado.web.RequestHandler):
    def get(self, sVial):
        logging.info("Printing label for " + sVial)
        sSql = f"""
        select v.notebook_ref batch_id, b.compound_id, IFNULL(v.conc, 'Solid')
        from glass.vial v, bcpvs.batch b
        where v.vial_id='{sVial}' and v.notebook_ref = b.notebook_ref
        """
        sSlask = cur.execute(sSql)
        tRes = cur.fetchall()
        if len(tRes) > 0:
            sDate = (time.strftime("%Y-%m-%d"))
            doPrint(tRes[0][1], tRes[0][0],
                    tRes[0][2], sDate, sVial)
            self.finish("Printed")
            return

def getNextVialId():
    sTmp = "V[0-9]+"

    sSql = 'select pkey from glass.vial_id_sequence'
    sSlask =  cur.execute(sSql)
    iVialPkey = cur.fetchall()[0][0]
    sNewVial = 'V' + str(iVialPkey).zfill(6)

    while True:
        sSql = f"""select vial_id from glass.vial where vial_id = '{sNewVial}'"""
        sSlask =  cur.execute(sSql)
        res = cur.fetchall()
        if len(res) == 1:
            iVialPkey += 1
            sNewVial = 'V' + str(iVialPkey).zfill(6)
        else:
            break
    sSql = f"""update glass.vial_id_sequence set pkey = {iVialPkey}"""
    sSlask =  cur.execute(sSql)
    return sNewVial


@jwtauth
class CreateEmptyVials(tornado.web.RequestHandler):
    def put(self, sNrOfVials):
        iNrOfVials = int(sNrOfVials)
        saResultingVials = []
        for i in range(iNrOfVials):
            sDate = (time.strftime("%Y-%m-%d"))
            sCmp = ""
            sBatch = ""
            sVial = getNextVialId()
            sType = '2'

            sSql = f"""insert into glass.vial
            (vial_id,
            type_id,
            updated_date)
            values ('{sVial}', 2, now())
            """
            try:
                sSlask = cur.execute(sSql)
                logVialChange(sVial, '', 'Created')
            except:
                sError = 'Vial already in database'
            doPrint(sCmp, sBatch, '', sDate, sVial)
            saResultingVials.append(sVial)
        self.write(json.dumps(saResultingVials))


@jwtauth
class DiscardPlate(tornado.web.RequestHandler):
    def put(self, sPlate):
        sSql = f"""update cool.plate set discarded = 1 where plate_id = '{sPlate}'"""
        sSlask = cur.execute(sSql)
        self.finish()


@jwtauth
class DiscardVial(tornado.web.RequestHandler):
    def put(self, sVial):
        sNull = 'NULL'
        sSql = f"""update glass.vial set location = 'SL11008', pos = {sNull}
        where vial_id = '{sVial}'"""
        sSlask = cur.execute(sSql)
        logVialChange(sVial, 'Discarding vial', 'Discarded')
        self.finish()


@jwtauth
class vialInfo(tornado.web.RequestHandler):
    def get(self, sVial):
        sSql = f"""SELECT notebook_ref batch_id from glass.vial where vial_id='%s'""" % sVial
        sSlask = cur.execute(sSql)
        tRes = cur.fetchall()
        lError = False
        if len(tRes) != 1:
            sError = 'Vial not found'
            self.set_status(400)
            self.finish(sError)
            logging.error('Vial ' + sVial + ' not found')
            return

        sSql = f"""select v.vial_id,
                   pos coordinate,
                   v.notebook_ref batch_id,
                   compound_id,
                   path box_id
               from glass.vial v
                  left join bcpvs.batch c ON v.notebook_ref = c.notebook_ref
                  left join loctree.v_all_locations l on v.location = l.loc_id
               where vial_id ='{sVial}'"""
        
        sSlask = cur.execute(sSql)
        tRes = cur.fetchall()
        self.write(json.dumps(res_to_json(tRes, cur)))


@jwtauth
class GetBoxLocation(tornado.web.RequestHandler):
    def get(self, sBox):
        sSlask = cur.execute(f"""SELECT name, path
                               FROM loctree.v_all_locations
                               where loc_id = '{sBox}'""")
        tRes = cur.fetchall()
        self.write(json.dumps(res_to_json(tRes, cur)))


def updateVialType(sBoxId, sVialId):
    sSql = """ SELECT vial_type FROM vialdb.box where box_id = %s """ % (sBoxId)
    sSlask = cur.execute(sSql)
    tType = cur.fetchall()
    sSql = """update vialdb.vial set
              vial_type = %s
              where vial_id = %s
           """ % (tType[0][0], sVialId)
    sSlask = cur.execute(sSql)


@jwtauth
class TransitVials(tornado.web.RequestHandler):
    def put(self, sVials):
        sIds = set(sVials.split())
        for sVialId in sIds:
            sOldBox, sOldName, sOldCoordinate = getVialPosition(sVialId)
            sLogString = f"""location from {sOldBox} {sOldName}:{sOldCoordinate}\
 to Compound collection"""
            logVialChange(sVialId, sLogString)
            logging.info(f'Placed {sVialId} in Compound collection')
            # Update the new location of the vial, SL11013 is 'Compound collection'
            sSql = f"""update glass.vial
                       set location = 'SL11013', pos = '', updated_date = now()
                       where vial_id = '{sVialId}'"""
            sSlask = cur.execute(sSql)


@jwtauth
class UpdateVialPosition(tornado.web.RequestHandler):
    def put(self, sVialId, sBoxId, sPos):
        sMessage = 'All ok'
        sBoxId = sBoxId.upper()
        if not re.search('v\d\d\d\d\d(\d|\d\d)', sVialId, re.IGNORECASE):
            self.set_status(400)
            jRes = getBoxFromDb(sBoxId)
            logging.error('Not a vial ' + sVialId)
            sMessage = 'Not a vial'
            jResult = [{'message':sMessage, 'data':jRes}]
            self.finish(json.dumps(jResult))
            return

        # Check if the position already is occupied by another compound
        sSql = f"""select vial_id from glass.vial
                  where location='{sBoxId}' and pos='{sPos}'
               """
        sSlask = cur.execute(sSql)
        tRes = cur.fetchall()
        if len(tRes) != 0:
            self.set_status(400)
            logging.error('this position is occupied ' + sBoxId + ' ' + sPos)
            sMessage = 'Position not empty'
            jResult = [{'message':sMessage}]
            self.finish(json.dumps(jResult))
            return
        sSql = f"""select name from loctree.locations where loc_id = '{sBoxId}'"""
        sSlask = cur.execute(sSql)
        tLoc = cur.fetchall()
        
        sOldBox, sOldName, sOldCoordinate = getVialPosition(sVialId)
        sLogString = f"""location from {sOldBox} {sOldName}:{sOldCoordinate}\
 to {sBoxId} {tLoc[0][0]}:{sPos}"""

        logVialChange(sVialId, sLogString)
        logging.info('Placed ' + sVialId + ' in ' + sBoxId)
        
        # Update the new location of the vial
        sSql = f"""update glass.vial
                   set location = '{sBoxId}', pos = '{sPos}', updated_date = now()
                   where vial_id = '{sVialId}'"""
        sSlask = cur.execute(sSql)

@jwtauth
class PrintPlate(tornado.web.RequestHandler):
    def get(self, sPlate):
        logging.info("Printing label for plate " + sPlate)
        doPrintPlate(sPlate)


@jwtauth
class printBox(tornado.web.RequestHandler):
    def get(self, sBox):

        sSql = f"""select v.name box_description, l.name vial_type_desc
        from loctree.v_all_locations v, loctree.location_type l
        where v.type_id = l.type_id and
        v.loc_id = '{sBox}'
        """
        #sSlask = cur.execute("""select box_description, vial_type_desc
        #                        from vialdb.box b, vialdb.vial_type v
        #                        where b.vial_type=v.vial_type
        #                        and box_id = '%s'""" % (sBox))
        cur.execute(sSql)
        tRes = cur.fetchall()
        sType = tRes[0][1]
        sDescription = tRes[0][0]

        zplVial = """^XA
^MMT
^PW400
^LL0064
^LS210
^CFA,20
^A0,25,20
^FO300,20^FDBox: %s^FS
^A0,25,20
^FO300,45^FDType: %s^FS
^A0,25,20
^FO300,70^FD%s^FS
^A0,25,20

^FX Third section with barcode.
^BY2,3,45
^FO300,95^BCN^FD%s^FS
^XZ
""" % (sBox.upper(), sType, sDescription, sBox.upper())

        f = open('/tmp/file.txt','w')
        f.write(zplVial)
        f.close()
        os.system("lp -h homer.scilifelab.se:631 -d CBCS-GK420t /tmp/file.txt")
        self.finish("Printed")


@jwtauth
class getBoxOfType(tornado.web.RequestHandler):
    def get(self, sBoxType):
        sSlask = cur.execute("""select distinct(p.box_id)
                           from vialdb.box_positions p, vialdb.box b
                           where p.box_id = b.box_id and
                           vial_type = '%s'""" % (sBoxType))
        tRes = cur.fetchall()
        #saRes = []
        #for saItem in tRes:
        #    saRes.append(saItem.box_id)
        self.write(json.dumps(res_to_json(tRes, cur)))


@jwtauth
class updateBox(tornado.web.RequestHandler):
    def get(self, sBox):
        self.set_header("Content-Type", "application/json")
        sSlask = cur.execute("""select box_id, box_description, vial_type_desc
                                from vialdb.box b, vialdb.vial_type t
                                where b.vial_type = t.vial_type and box_id = '%s'
               """ % (sBox))
        tRes = cur.fetchall()
        jRes = getBoxFromDb(sBox)
        try:
            jResult = [{'message':'Box type:' + tRes[0][2] + ', Description:' + tRes[0][1],
                        'data':jRes}]
            self.write(json.dumps(jResult))
        except:
            self.set_status(400)
            self.finish(json.dumps("Box not found"))

@jwtauth
class GetBox(tornado.web.RequestHandler):
    def get(self, sBox):
        jRes = getBoxFromDb(sBox)
        try:
            #jResult = [{'message':'Box type:' + tRes[0][2] + ', Description:' + tRes[0][1],
            #            'data':jRes}]
            #self.write(json.dumps(jResult))
            jResult = [{'data':jRes}]
            self.write(json.dumps(jRes))
        except:
            self.set_status(400)
            self.finish(json.dumps("Box not found"))


@jwtauth
class searchVials(tornado.web.RequestHandler):
    def get(self, sVials):
        sIds = set(sVials.split())
        tmpIds = ""
        jRes = []
        lNotFound = list()
        for sId in sIds:
            sSql = f"""
            SELECT
            v.vial_id AS vialId,
            v.notebook_ref AS batchId,
            c.compound_id AS compoundId,
            v.location AS boxId,
            l.name AS boxDescription,
            l.path,
            v.pos,
            c.biological_mw AS batchMolWeight,
            ROUND(((v.net*1000/c.biological_mw)/v.conc)*1000000) AS dilution
            FROM
	    glass.vial v
            left join bcpvs.batch c ON v.notebook_ref = c.notebook_ref
            LEFT OUTER JOIN loctree.v_all_locations l on v.location = l.loc_id
            WHERE v.vial_id = '{sId}'
            """

            try:
                sSlask = cur.execute(sSql)
            except Exception as e:
                logging.error("Error: " + str(e))
                
                self.set_status(400)
                self.finish()
                return
            tRes = cur.fetchall()
            if len(tRes) != 1:
                lNotFound.append(sId)
                jRes.append({"vialId":sId,
                             "pos":'',
                             "path":'',
                             "batchId":'',
                             "compoundId":'',
                             "cbkId":'',
                             "boxId":'Vial not in DB',
                             "boxDescription":'Vial not in DB',
                             "batchMolWeight":'',
                             "dilution":''})
                continue
            #for row in tRes:
            #    jRes.append({"vialId":row.vial_id,
            #                 "coordinate":row.coordinate,
            #                 "batchId":row.batch_id,
            #                 "compoundId":row.compound_id,
            #                 "cbkId":row.cbk_id,
            #                 "boxId":row.box_id,
            #                 "batchMolWeight":row.batch_formula_weight,
            #                 "dilution":row.dilution})
            jRes.append(res_to_json(tRes, cur)[0])
        self.finish(json.dumps(jRes))


@jwtauth
class VerifyLocation(tornado.web.RequestHandler):
    def get(self, sLocation):
        sSql = f"""
        select * from loctree.locations where loc_id = '{sLocation}'
        """
        cur.execute(sSql)
        tRes = cur.fetchall()
        if len(tRes) != 1:
            self.set_status(400)
            self.finish('Unknown location')
        else:
            self.finish()
            

@jwtauth
class searchBatches(tornado.web.RequestHandler):
    def get(self, sBatches):
        sIds = list(set(sBatches.split()))
        jRes = []

        tmpIds = ""
        for sId in sIds:
            tmpIds += "'" + sId + "'"
        stringIds = tmpIds.replace("''", "','")
        if sIds[0].startswith('CBK'):
            sSql = """
            SELECT v.notebook_ref as batchId,
            c.compound_id as compoundId,
            v.location as boxId,
            l.name as boxDescription,
            l.path,
            v.pos,
            v.vial_id vialId,
            c.biological_mw as batchMolWeight
            FROM glass.vial v,
            bcpvs.batch c,
            loctree.v_all_locations l
            where
	    v.notebook_ref = c.notebook_ref and
            l.loc_id = v.location and
            c.compound_id = %s
            """
        else:
            sSql = """
            SELECT v.notebook_ref as batchId,
            c.compound_id as compoundId,
            v.location as boxId,
            l.name as boxDescription,
            l.path,
            v.pos,
            v.vial_id vialId,
            c.biological_mw as batchMolWeight
            FROM glass.vial v,
            bcpvs.batch c,
            loctree.v_all_locations l
            where
	    v.notebook_ref = c.notebook_ref and
            l.loc_id = v.location and
            v.notebook_ref = %s
            """
        for sId in sIds:
            sSlask = cur.execute(sSql, [sId])
            tRes = cur.fetchall()
            if len(tRes) == 0:
                jRes.append({"vialId":sId,
                             "coordinate":'',
                             "batchId":'',
                             "compoundId":'',
                             "cbkId":'',
                             "boxId":'Not found',
                             "batchMolWeight":''})
                continue
            #for row in tRes:
            #    jRes.append({"vialId":row.vial_id,
            #                 "coordinate":row.coordinate,
            #                 "batchId":row.batch_id,
            #                 "compoundId":row.compound_id,
            #                 "cbkId":row.cbk_id,
            #                 "boxId":row.box_id,
            #                 "batchMolWeight":row.batch_formula_weight})
            #jRes.append(res_to_json(tRes, cur)[0])
            tmp = res_to_json(tRes, cur)
            for i in tmp:
                jRes.append(i)
        self.finish(json.dumps(jRes))


@jwtauth
class DeleteLocation(tornado.web.RequestHandler):
    def put(self, sLocation):
        sSlask = cur.execute(f"""
        select * from loctree.locations where parent = '{sLocation}'
        """)
        tRes = cur.fetchall()
        if len(tRes) != 0:
            self.set_status(400)
            self.finish(f'{sLocation} not empty, location has sublocations')
            return
        
        sSlask = cur.execute(f"""
        select * from glass.vial where location = '{sLocation}'
        """)
        tRes = cur.fetchall()
        if len(tRes) != 0:
            self.set_status(400)
            self.finish(f'Vials in {sLocation}, location not empty')
            return
        
        sSlask = cur.execute(f"""
        select * from microtube.matrix where location = '{sLocation}'
        """)
        tRes = cur.fetchall()
        if len(tRes) != 0:
            self.set_status(400)
            self.finish(f'Matrix location {sLocation} not empty')
            return

        sSlask = cur.execute(f"""
        delete from loctree.locations where loc_id = '{sLocation}'
        """)


@jwtauth
class GetFreeBoxes(tornado.web.RequestHandler):
    def get(self):
        sSql = f"""
        select ll.loc_id location,
        FORMAT(ll.subpos - IFNULL(v_count, 0), 0) free_positions,
        ll.path, ll.loc_type, ll.name name
        from
        (select location, count(vial_id) v_count
        from glass.vial group by location) v
        right outer join
        (select l.loc_id, t.subpos, l.name, l.path, t.name loc_type
        from loctree.v_all_locations l, loctree.location_type t
        where l.type_id = t.type_id
        and t.subpos is not null and t.subpos < 300) ll
        on v.location = ll.loc_id  order by path, free_positions
        """

        sSlask = cur.execute(sSql)
        tRes = cur.fetchall()
        self.write(json.dumps(res_to_json(tRes, cur)))
        

@jwtauth
class CreateMolImage(tornado.web.RequestHandler):
    def get(self, sId):
        if exists(f'mols/{sId}.png'):
            self.finish()
            return
        sId = sId.lower()
        m = re.search("v\d\d\d\d\d\d", sId)
        sSql = ""
        if m:
            sSql = f"""select mol
            from bcpvs.JCMOL_MOLTABLE m, glass.vial v, bcpvs.batch c
            where v.notebook_ref = c.notebook_ref
            and c.compound_id = m.compound_id and
            vial_id = '{sId}'
            """
        else:
            sId = sId.upper()
            m = re.search("CBK\d\d\d\d\d\d", sId)
            if m:
                sSql = f"""select mol
                from bcpvs.JCMOL_MOLTABLE m
                where
                m.compound_id = '{sId}'
                """
            else:
                sSql = f"""
                select mol
                from bcpvs.JCMOL_MOLTABLE m, bcpvs.batch b
                where
                m.compound_id = b.compound_id and
                b.notebook_ref = '{sId}'
                """
        if sSql != "":
            cur.execute(sSql)
            molfile = cur.fetchall()
            if len(molfile) > 0 and molfile[0][0] != None:
                createPngFromMolfile(sId.upper(), molfile[0][0])
        self.finish()


class GetDatabase(tornado.web.RequestHandler):
    def get(self):
        sRes = json.dumps([['Live'], ['Test']])
        self.finish(sRes)


@jwtauth
class GetLocationByStorage(tornado.web.RequestHandler):
    def get(self, sStorage):
        if sStorage == 'Freezer':
            sSql = f"""select loc_id, path from loctree.v_all_locations
            where type_id in (29, 31, 69, 6, 8, 24, 25, 27) order by type_id, path
            """
        else:
            sSql = f"""select loc_id, path from loctree.v_all_locations
            where type_id in (7, 9) order by type_id, path"""

        cur.execute(sSql)
        tRes = cur.fetchall()
        self.write(json.dumps(res_to_json(tRes, cur)))


@jwtauth
class GetLocationPath(tornado.web.RequestHandler):
    def get(self, sLocation):
        sSql = f'''
        select l.loc_id, l.path
        from loctree.v_all_locations l
        where
        l.loc_id = '{sLocation}'
        or l.name = '{sLocation}'
        '''
        cur.execute(sSql)
        tRes = cur.fetchall()
        self.write(json.dumps(res_to_json(tRes, cur)))


@jwtauth
class GetLocationChildren(tornado.web.RequestHandler):
    def get(self, sLocation):
        if sLocation == 'root':
            sSql = f'''
            select l.loc_id, l.name, l.path, t.name type, t.use_subpos has_children
            from loctree.v_all_locations l, loctree.location_type t
            where l.type_id = t.type_id and
            l.parent is null'''        
        else:
            sSql = f'''
            select l.loc_id, l.name, l.path, t.name type, t.use_subpos has_children
            from loctree.v_all_locations l, loctree.location_type t
            where l.type_id = t.type_id and
            l.parent = '{sLocation}'
            '''
        cur.execute(sSql)
        tRes = cur.fetchall()
        self.write(json.dumps(res_to_json(tRes, cur)))


@jwtauth
class AddBox(tornado.web.RequestHandler):
    def put(self, sParent, sBoxName, sBoxSize):
        sNewLocId = getNewLocId()
        if sBoxSize == '200':
            loc_type = 10
        elif sBoxSize == '50':
            loc_type = 18
        elif sBoxSize == '64':
            loc_type = 32
        elif sBoxSize == 'Matrix':
            loc_type = 7

        sSql = f'''
        insert into loctree.locations (loc_id, parent, type_id, created_date, name)
        values 
        ('{sNewLocId}', '{sParent}', '{loc_type}', now(), '{sBoxName}')
        '''
        cur.execute(sSql)


@jwtauth
class AddLocation(tornado.web.RequestHandler):
    def put(self, sParent, sLocationName, sLocationType):
        sNewLocId = getNewLocId()
        if sLocationType == 'Room':
            loc_type = 3
        elif sLocationType == 'Fridge-Freezer':
            loc_type = 24
        elif sLocationType == 'Shelf':
            loc_type = 7
            
        sSql = f'''
        insert into loctree.locations (loc_id, parent, type_id, created_date, name)
        values 
        ('{sNewLocId}', '{sParent}', '{loc_type}', now(), '{sLocationName}')
        '''
        cur.execute(sSql)


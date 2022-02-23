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

db = mydb.DisconnectSafeConnection()
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


class home(util.UnsafeHandler):
    def get(self, *args, **kwargs):
        return

def getNewLocId():
    sSql = f"select pkey from loctree.location_id_sequence"
    cur.execute(sSql)
    pkey = cur.fetchall()[0][0] +1
    sSql = f"update loctree.location_id_sequence set pkey={pkey}"
    cur.execute(sSql)
    return 'SL' + str(pkey)


@jwtauth
class getMicroTubeByBatch(tornado.web.RequestHandler):
    def get(self, sBatches):
        if len(sBatches) < 1:
            print("no batch")
            self.write(json.dumps({}))
            return
        saBatches = sBatches.split()
        saBatches = list(set(saBatches))
        logging.info(saBatches)
        jResTot = list()
        sTmp = '","'

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
            sId = sId.replace('KI_', '')
            sSql = """select
                      t.notebook_ref as batchId, t.tube_id as tubeId, t.volume*1000000 as volume,
                      m.matrix_id as matrixId, mt.position as position, m.location as location
                      from microtube.tube t, microtube.v_matrix_tube mt, microtube.v_matrix m
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
            
            jRes = makeJson(tRes, jRes, sId)
        self.write(json.dumps(jRes, indent=4))


@jwtauth
class ReadScannedRack(tornado.web.RequestHandler):
    def post(self):
        try:
            # self.request.files['file'][0]:
            # {'body': 'Label Automator ___', 'content_type': u'text/plain', 'filename': u'k.txt'}
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
                    saError.append(sTube)
                    err = str(e)
                    logging.error(f'Failed updating tube {err}')
                    print(f'Failed updating tube {sTube} {err}')
            iOk += 1
        self.finish(json.dumps({'FailedTubes': saError,
                                'iOk': iOk,
                                'iError': iError,
                                'sRack': sRackId
        }))


@jwtauth
class getRack(tornado.web.RequestHandler):
    def get(self, sRack):
        logging.info(sRack)
        jResTot = list()
        sTmp = '","'

        def makeJson(tData, jRes, sId):
            if len(tData) == 0:
                return jRes
            iRow = 0
            for row in tData:
                try:
                    sSql = """
                    select notebook_ref from bcpvs.batch where
                    notebook_ref = '%s' or notebook_ref = '%s'
                    """ % ('UU_' + row[0], 'KI_' + row[0]) # matrixId
                    sSlask = cur.execute(sSql)
                    tSsl = cur.fetchall()
                    sSll = None
                    tSsl = ('test')
                    if len(tSsl) != 0:
                        sSll = tSsl
                    else:
                        sSll = ''
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
                                    "ssl": sSll,
                                    "iRow" : sRow
                    })
                    iRow += 1
                except Exception as e:
                    logging.error('Failed at appending ' + sId + ' ' + str(e))
            return jRes

        jRes = list()
        sSql = """select
                  t.notebook_ref as batchId, t.tube_id as tubeId, t.volume*1000000 as volume,
                  m.matrix_id as matrixId, mt.position as position, m.location as location,
                  t.conc * 1000, compound_id, SUBSTR(mt.position, 2,3) as rackrow
                  from microtube.tube t, microtube.v_matrix_tube mt, microtube.v_matrix m , bcpvs.batch b
                  where
                  t.notebook_ref  = b.notebook_ref and
                  t.tube_id = mt.tube_id and
                  m.matrix_id = mt.matrix_id and
                  mt.matrix_id = '%s' order by rackrow, position""" % sRack
        try:
            sSlask = cur.execute(sSql)
            tRes = cur.fetchall()
        except Exception as e:
            logging.error("Error: " + str(e) + ' problem with rack:' + sRack)
            return
            
        jRes = makeJson(tRes, jRes, sRack)
        self.write(json.dumps(jRes, indent=4))

        
@jwtauth
class uploadEmptyVials(tornado.web.RequestHandler):
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
        output_file = open("uploads/" + original_fname, 'w')
        output_file.write(file1['body'])
        output_file.close()

        fNewFile = open(finalFilename, mode='rU')
        saFile = fNewFile.readlines()
        iOk = 0
        iError = 0
        saError = []
        for sLine in saFile:
            saLine = sLine.split('\t')
            #logging.info(saLine)

            if len(saLine) == 4 or len(saLine) == 2:
                sVial = ''.join(saLine[0].split())
                m = re.search(r'V\d\d\d\d\d(\d|\d\d)', sVial)
                if m:
                    sTare = ''.join(saLine[1].split())
                    try:
                        sSql = f"""insert into vialdb.vial (vial_id, tare, update_date) 
                                   values ({sVial}, {sTare}, now())"""
                        sSlask = cur.execute(sSql)
                        iOk += 1
                    except:
                        iError += 1
                        saError.append(sVial)
                        sSql = f"""update vialdb.vial set
                                   tare = {sTare},
                                   update_date = now()
                                   where vial_id = {sVial}
                        """
                        logging.info("Upload vial: " + sVial + ' Tare: ' + sTare)
                        sSlask = cur.execute(sSql)

        self.finish(json.dumps({'FailedVials':saError, 'iOk':iOk, 'iError':iError}))

def getNewLocationId():
    sSlask = cur.execute("""SELECT pk, location_id, location_description
                            from vialdb.box_location
                            order by pk desc limit 1""")
    tRes = cur.fetchall()
    if len(tRes) == 0:
        iKey = 0
    else:
        iKey = tRes[0].pk
    sKey = '%05d' % (iKey + 1)
    sLoc = 'DP' + sKey
    return sLoc

def getNewBoxId():
    sSlask = cur.execute("""SELECT pk from vialdb.box order by pk desc limit 1""")
    tRes = cur.fetchall()
    if len(tRes) == 0:
        iKey = 0
    else:
        iKey = tRes[0].pk
    sKey = '%05d' % (iKey + 1)
    sLoc = 'DB' + sKey
    return sLoc

def deleteOldVialPosition(sVialId):
    sSql = f"""update vialdb.box_positions set
               vial_id={None},
               update_date=now()
               where vial_id={sVialId}
    """
    sSlask = cur.execute(sSql)

def logVialChange(sVialId, sLogMessage, sNewPos=None):
    sSql = f"""
    insert into glass.vial_log (vial_id, updated_date, changes)
    values ('{sVialId}', now(), '{sLogMessage}')
    """
    try:
        sSlask = cur.execute(sSql)
    except:
        pass

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
^BY1,3,45
^FO490,30^BCR^FD%s^FS
^XZ
""" % (sCmp, sBatch, sType, sDate, sVial, sVial)
    f = open('/tmp/file.txt','w')
    f.write(zplVial)
    f.close()
    os.system("lp -h homer.scilifelab.se:631 -d CBCS-GK420d /tmp/file.txt")


@jwtauth
class createLocation(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        self.set_header("Content-Type", "application/json")
        try:
            sDescription = self.get_argument("description", default='', strip=False)
        except:
            logging.error("Error cant find file1 in the argument list")
            return
        sLoc = getNewLocationId()
        sSql = f"""insert into vialdb.box_location (location_id,
                   location_description, update_date)
                   values ({sLoc}, {sDescription}, now())"""
        sSlask = cur.execute(sSql)
        self.write(json.dumps({'locId':sLoc,
                               'locDescription':sDescription}))

@jwtauth
class getLocations(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        self.set_header("Content-Type", "application/json")
        sSlask = cur.execute("""SELECT location_id, location_description
                                from vialdb.box_location
                                order by pk""")
        tRes = cur.fetchall()
        self.write(json.dumps(res_to_json(tRes, cur), indent=4))


@jwtauth
class searchLocation(tornado.web.RequestHandler):
    def get(self, sLocation):
        self.set_header("Content-Type", "application/json")
        sSlask = cur.execute("""
                     SELECT l.location_id as locId,
                           location_description as locDescription,
                           box_id as boxId,
                           box_description as boxDescription
                           from vialdb.box_location l
                 	   left join vialdb.box b
                           on l.location_id = b.location_id
                           where l.location_id = '%s'""" % (sLocation))
        tRes = cur.fetchall()
        #jRes = []
        #for row in tRes:
        #    jRes.append({"locId":row.location_id,
        #                 "locDescription":row.location_description,
        #                 "boxId":row.box_id,
        #                 "boxDescription":row.box_description})
        self.write(json.dumps(res_to_json(tRes, cur)))


@jwtauth
class verifyVial(tornado.web.RequestHandler):
    def get(self, sVial):
        sSql = f"""SELECT batch_id, vial_type
                  from vialdb.vial
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

        sSlask = cur.execute("""
                  SELECT v.vial_id sVial, v.batch_id, v.vial_type,
                  b.compound_id,
                  v.tare, batch_formula_weight,
                  net iNetWeight, gross iGross,
                  dilution iDilutionFactor
                  from vialdb.vial v
                  left outer join ddd.batch b on v.batch_id = b.batch_id
                  where  v.vial_id = '%s'
        """ % (sVial))
        tRes = cur.fetchall()
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
class editVial(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        sCompoundId = self.get_argument("compound_id")
        sVial = self.get_argument("sVial")
        sBatch = self.get_argument("batch_id")
        sBoxType = self.get_argument("sBoxType[vial_type]")
        sTare = self.get_argument("tare")
        sGross = self.get_argument("iGross")
        sNetWeight = self.get_argument("iNetWeight")
        iDilutionFactor = self.get_argument("iDilutionFactor")

        #logging.info(self.request.arguments.values())

        sSql = """
        update vialdb.vial set
        batch_id = %s,
        compound_id = %s,
        vial_type = %s,
        update_date = now(),
        tare = %s,
        net = %s,
        gross = %s,
        dilution = %s
        where vial_id = %s
        """ % (sBatch, sCompoundId, sBoxType, sTare,
               sNetWeight, sGross, iDilutionFactor, sVial)

        try:
            cur.execute(sSql)
        except Exception as e:
            logging.error("Error updating vial " + str(sVial))
            logging.error("Error: " + str(e))
        logging.info("Done editing vial: " + str(sVial))
        return


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
    sTmp = "V%"
    sSql = """select vial_id from vialdb.vial where vial_id like %s
              order by LENGTH(vial_id) DESC, vial_id desc limit 1""" % (sTmp)
    sSlask =  cur.execute(sSql)
    sVial = cur.fetchall()
    try:
        sVial = sVial[0]['vial_id']
    except:
        logging.error(sVial)
        
    try:
        iVial = int(sVial.split('V')[1])
    except:
        logging.error("Error in getNextVialId " + sVial)
        return
    sNewVial = 'V' + str(iVial + 1).zfill(7)
    return sNewVial


@jwtauth
class createManyVialsNLabels(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        iNumberOfVials = int(self.get_argument("numberOfVials",
                                               default='',
                                               strip=False))
        sType = self.get_argument("vialType", default='', strip=False)
        sSql = """SELECT vial_type_desc FROM vialdb.vial_type
                  where vial_type = %s""" % (sType)
        sSlask = cur.execute(sSql)[0]['vial_type_desc']
        sTypeDesc = cur.fetchall()
        for i in range(iNumberOfVials):
            sDate = (time.strftime("%Y-%m-%d"))
            sCmp = ""
            sBatch = ""
            sVial = getNextVialId()
            
            sSql = """insert into vialdb.vial
            (vial_id,
            vial_type,
            update_date,
            checkedout)
            values ('%s', '%s', now(), '%s')
            """ % (sVial, sType, 'Unused')
            try:
                sSlask = cur.execute(sSql)
                logVialChange(sVial, '', 'Created')
            except:
                sError = 'Vial already in database'
            doPrint(sCmp, sBatch, sTypeDesc, sDate, sVial)


@jwtauth
class generateVialId(tornado.web.RequestHandler):
    def get(self):
        sNewVial = getNextVialId()
        self.write(json.dumps({'vial_id':sNewVial}))


@jwtauth
class discardVial(tornado.web.RequestHandler):
    def get(self, sVial):
        sSql = """update vialdb.box_positions set vial_id=%s,
                  update_date=now()
                  where vial_id=%s""" % (None, sVial)
        sSlask = cur.execute(sSql)
        sSql = """update vialdb.vial set discarded='Discarded',
                  update_date=now(), checkedout=%s
                  where vial_id=%s""" % (None, sVial)
        sSlask = cur.execute(sSql)
        logVialChange(sVial, '', 'Discarded')
        self.finish()


@jwtauth
class vialInfo(tornado.web.RequestHandler):
    def get(self, sVial):
        sSql = f"""SELECT batch_id from vialdb.vial where vial_id='%s'""" % sVial
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
class getVialTypes(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        sSlask = cur.execute("""SELECT vial_type, vial_type_desc, concentration
                                from vialdb.vial_type
                                order by vial_order asc""")
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
^CFA,20
^A0,25,20
^FO295,20^FDBox: %s^FS
^A0,25,20
^FO295,45^FDType: %s^FS
^A0,25,20
^FO295,70^FD%s^FS
^A0,25,20

^FX Third section with barcode.
^BY1,3,45
^FO490,30^BCR^FD%s^FS
^XZ
""" % (sBox.upper(), sType, sDescription, sBox.upper())
        f = open('/tmp/file.txt','w')
        f.write(zplVial)
        f.close()
        os.system("lp -h homer.scilifelab.se:631 -d CBCS-GK420d /tmp/file.txt")
        self.finish("Printed")


@jwtauth
class createBox(tornado.web.RequestHandler):
    def createVials(self, sBoxId, iVialPk):
        for iVial in range(NR_OF_VIALS_IN_BOX):
            iCoord = iVial + 1
            sSql = """insert into vialdb.box_positions
                      (box_id, coordinate, update_date)
                      values (%s, %s, now())""" % (sBoxId, iCoord)
            sSlask = cur.execute(sSql)

    def post(self, *args, **kwargs):
        try:
            sDescription = self.get_argument("description", default='', strip=False)
            sType = self.get_argument("type", default='', strip=False)
            sLocation = self.get_argument("location", default='', strip=False)
            sSlask = cur.execute("""SELECT vial_type from vialdb.vial_type
                               where vial_type_desc = '%s'""" % (sType))[0].vial_type
            iVialPk = cur.fetchall()
        except:
            logging.error("Error cant find description or type in the argument list")
            logging.error(sDescription)
            logging.error("sType " + sType)
            logging.error("sLocation " + sLocation)
            return
        sBox = getNewBoxId()
        sSql = """insert into vialdb.box (box_id, box_description, vial_type,
                  location_id, update_date) values (%s, %s, %s, %s, now())"""
        sSlask = cur.execute(sSql, sBox, sDescription, iVialPk, sLocation)
        self.createVials(sBox, iVialPk)
        self.write(json.dumps({'boxId':sBox,
                               'boxDescription':sDescription}))
        zplVial = """^XA
^CFA,20
^A0,25,20
^FO295,20^FDBox: %s^FS
^A0,25,20
^FO295,45^FDType: %s^FS
^A0,25,20
^FO295,70^FD%s^FS
^A0,25,20

^FX Third section with barcode.
^BY1,3,45
^FO490,30^BCR^FD%s^FS
^XZ
""" % (sBox.upper(), sType, sDescription, sBox.upper())
        f = open('/tmp/file.txt','w')
        f.write(zplVial)
        f.close()
        os.system("lp -h homer.scilifelab.se:631 -d CBCS-GK420d /tmp/file.txt")
        self.finish("Printed")


@jwtauth
class getFirstEmptyCoordForBox(tornado.web.RequestHandler):
    def get(self, sBox):
        sSlask = cur.execute("""select coordinate from vialdb.box_positions
                                where (vial_id is null or vial_id ='')
                                and box_id = '%s'
                                order by coordinate asc limit 1""" % (sBox))
        tRes = cur.fetchall()
        self.write(json.dumps(res_to_json(tRes, cur)))


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
class searchBatches(tornado.web.RequestHandler):
    def get(self, sBatches):
        sIds = sBatches.split()
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
            jRes.append(res_to_json(tRes, cur)[0])
        self.finish(json.dumps(jRes))


@jwtauth
class getLocation(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        sSlask = cur.execute("SET CHARACTER SET utf8")
        self.set_header("Content-Type", "application/json;charset=utf-8")
        sSlask = cur.execute("select vial_location from vialdb.vial_location")
        tRes = cur.fetchall()
        tRes = list(tRes)
        tRes.insert(0, {'vial_location': u''})
        tRes = tuple(tRes)
        #tRes = {'vial_location': u''}.update(tRes)
        self.write(json.dumps(res_to_json(tRes, cur),
                              ensure_ascii=False).encode('utf8'))


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
class MoveVialToLocation(tornado.web.RequestHandler):
    def get(self, sVial, sUser):
        sSlask = cur.execute("""
          select vial_location
          from vialdb.vial_location
          where vial_location = '%s'""" % sUser)
        tRes = cur.fetchall()
        if len(tRes) != 1:
            return
        sUser = tRes[0].vial_location

        sOldBox, sOldCoordinate, sCheckedOut = getVialPosition(sVial)
        sOldPos = ""

        if sOldBox != '':
            sOldPos = sOldBox + ' ' + sOldCoordinate
        else:
            sOldPos = sCheckedOut
        logVialChange(sVial, sOldPos, sUser)

        # Reset discarded flag if it was set 
        sSql = """update vialdb.vial set 
                  discarded=%s, 
                  update_date=now() 
                  where vial_id=%s 
               """ % (None, sVial)
        sSlask = cur.execute(sSql)

        # Erase the old place of the vial
        deleteOldVialPosition(sVial)
 
        sSql = """update vialdb.vial set 
                  checkedout = %s 
                  where vial_id = %s 
               """ % (sUser, sVial)
        sSlask = cur.execute(sSql)


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



        '''
        select location, FORMAT(FLOOR(subpos-count(vial_id)), 0) free_positions,
        min(path) path, min(loctree.location_type.name) loc_type, loctree.locations.name
        from glass.vial, loctree.locations, loctree.location_type, loctree.v_all_locations
        where 
        glass.vial.location = loctree.locations.loc_id
        and loctree.locations.type_id = loctree.location_type.type_id
        and glass.vial.location = loctree.v_all_locations.loc_id
        and loctree.location_type.label_format = 'VIAL_TRAY.pj'
        and subpos is not null and subpos < 300
        group by glass.vial.location order by path"""
        '''

        sSlask = cur.execute(sSql)
        tRes = cur.fetchall()
        self.write(json.dumps(res_to_json(tRes, cur)))
        
@jwtauth
class CreateMolImage(tornado.web.RequestHandler):
    def get(self, sId):
        sId = sId.lower()
        m = re.search("v\d\d\d\d\d\d", sId)
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


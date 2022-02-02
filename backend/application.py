import tornado.gen
import MySQLdb 
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
import config

db_connection = MySQLdb.connect(
    host=config.database['host'],
    user=config.database['user'],
    passwd=config.database['password'],
    database=config.database['db']
)

db_connection.autocommit(True)
cur = db_connection.cursor()

NR_OF_VIALS_IN_BOX = 200

def res_to_json(response, cursor):
    columns = cursor.description 
    to_js = [{columns[index][0]:column for index, column in enumerate(value)} for value in response]
    return to_js


class home(util.UnsafeHandler):
    def get(self, *args, **kwargs):
        return


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
class readScannedRack(tornado.web.RequestHandler):
    def post(self):
        try:
            # self.request.files['file'][0]:
            # {'body': 'Label Automator ___', 'content_type': u'text/plain', 'filename': u'k.txt'}
            file1 = self.request.files['file'][0]
        except:
            logging.error("Error cant find file1 in the argument list")
            return

        m = re.search("Rack Base Name: (\w\w\d+)", file1['body'])
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
        output_file.write(file1['body'])
        output_file.close()

        fNewFile = open(finalFilename, mode='rU')
        saFile = fNewFile.readlines()
        iOk = 0
        iError = 0
        saError = []
        for sLine in saFile:
            m = re.search("  (\w\d\d);\t(\d+)", sLine)
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
                iError += 1
                saError.append(sTube)
                logging.info("tube_id " + sTube + ' does not exists')
                continue
            sSql = """update microtube.matrix_tube set position = '%s', matrix_id = '%s'
                      where tube_id = '%s'
                   """ % (sPosition, sRackId, sTube)
            sSlask = cur.execute(sSql)
            #con.commit()
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

def logVialChange(sVialId, sOldPos, sNewPos):
    sSql = f"""
    insert into vialdb.vial_log (vial_id, old_location, new_location)
    values ({sVialId}, {sOldPos}, {sNewPos})
    """
    sSlask = cur.execute(sSql)

def getVialPosition(sVialId):
    sSql = f"""select IFNULL(b.box_id, '') box_id,
               IFNULL(b.coordinate, '') coordinate, v.checkedout
               from vialdb.vial v
               left outer join vialdb.box_positions b on v.vial_id = b.vial_id
               where v.vial_id={sVialId}
    """
    sSlask = cur.execute(sSql)
    tRes = cur.fetchall()
    logging.info(tRes)
    if len(tRes) == 0:
        return '', '', ''
    return str(tRes[0].box_id).upper(), str(tRes[0].coordinate), tRes[0].checkedout

def getBoxFromDb(sBox):
    sSlask = cur.execute("""SELECT v.vial_id, coordinate, batch_id, compound_id,
                       b.box_id, box_description
                       from vialdb.box b
                       left join vialdb.box_positions v on b.box_id = v.box_id
                       left join vialdb.vial c on v.vial_id = c.vial_id
                       where b.box_id = '%s' order by coordinate asc""" % (sBox))
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
        sSql = """
               select batch_id, compound_id, vial_type_desc
               from vialdb.vial_type vt, vialdb.vial v
               where v.vial_id=%s and v.vial_type = vt.vial_type
        """ % (sVial)
        sSlask = cur.execute(sSql)
        tRes = cur.fetchall()
        if len(tRes) > 0:
            sDate = (time.strftime("%Y-%m-%d"))
            doPrint(tRes[0].compound_id, tRes[0].batch_id,
                    tRes[0].vial_type_desc, sDate, sVial)
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

        sSql = """SELECT v.vial_id, coordinate, v.batch_id, v.compound_id,
                  b.box_id,box_description, v.tare, discarded, checkedout
	          from vialdb.vial v left join bcpvs.batch c on v.batch_id = c.notebook_ref
                  left join vialdb.box_positions p on v.vial_id = p.vial_id
                  left join vialdb.box b on p.box_id = b.box_id
                  where v.vial_id='%s'""" % sVial
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
class getBoxDescription(tornado.web.RequestHandler):
    def get(self, sBox):
        sSlask = cur.execute("""SELECT box_description FROM vialdb.box where box_id = '%s'""" % (sBox))
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
class updateVialPosition(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        sVialId = self.get_argument("vialId", default='', strip=False)
        sBoxId = self.get_argument("boxId", default='', strip=False)
        iCoordinate = self.get_argument("coordinate", default='', strip=False)
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
        sSql = """select vial_id from vialdb.box_positions
                  where box_id=%s and coordinate=%s
               """ % (sBoxId, iCoordinate)
        sSlask = cur.execute(sSql)
        tRes = cur.fetchall()
        if len(tRes) != 1 or tRes[0].vial_id != None:
            self.set_status(400)
            jRes = getBoxFromDb(sBoxId)
            logging.error('this position is occupied ' + sBoxId + ' ' + iCoordinate)
            sMessage = 'Position not empty'
            jResult = [{'message':sMessage, 'data':jRes}]
            self.finish(json.dumps(jResult))
            return

        # Check if the vial has the same type as the box to be placed in
        sSql = """select v.vial_type
                  from vialdb.box b, vialdb.vial v
                  where (b.vial_type = v.vial_type or v.vial_type is null) and vial_id = %s and box_id = %s
               """ % (sVialId, sBoxId)
        sSlask = cur.execute(sSql)
        tRes = cur.fetchall()

        if len(tRes) != 1:
            self.set_status(400)
            jRes = getBoxFromDb(sBoxId)
            sMessage = 'Vial not found ' + sVialId
            logging.error(sMessage)
            jResult = [{'message':sMessage, 'data':jRes}]
            self.finish(json.dumps(jResult))
            return

        if tRes[0][0] == None:
            updateVialType(sBoxId, sVialId)
            logging.error('Please update vialtype here to same as the box ' + sVialId + ' ' + sBoxId)
            
        sOldBox, sOldCoordinate, sCheckedOut = getVialPosition(sVialId)
        sOldPos = ""
        if sOldBox != '':
            sOldPos = sOldBox + ' ' + sOldCoordinate
        else:
            sOldPos = sCheckedOut
        logVialChange(sVialId, sOldPos, sBoxId + ' ' + iCoordinate)
        logging.info('Placed ' + sVialId + ' in ' + sBoxId)
        # Erase the old place of the vial
        deleteOldVialPosition(sVialId)

        # Update the new location of the vial
        sSql = """update vialdb.box_positions set
                  vial_id=%s,
                  update_date=now()
                  where box_id=%s and coordinate=%s
               """ % (sVialId, sBoxId, iCoordinate)
        sSlask = cur.execute(sSql)

        # Make sure that the vial isn't checkedout anymore
        sSql = """update vialdb.vial set
                  checkedout=%s,
                  update_date=now()
                  where vial_id=%s
               """ % (None, sVialId)
        sSlask = cur.execute(sSql)

        jRes = getBoxFromDb(sBoxId)
        #self.finish(json.dumps(jRes))

        sSlask = cur.execute("""SELECT v.vial_id as vialId,
                                coordinate, batch_id as batchId,
                                compound_id as compoundId,
                                b.box_id as boxId,
                                box_description as boxDescription
                                from vialdb.box b
                                left join vialdb.box_positions v on b.box_id = v.box_id
                                left join vialdb.vial c on v.vial_id = c.vial_id
                                where b.box_id = '%s'
                                and coordinate = '%s'""" % (sBoxId, iCoordinate))
        tRes = cur.fetchall()
        #jRes = {"vialId":tRes[0].vial_id,
        #        "coordinate":tRes[0].coordinate,
        #        "batchId":tRes[0].batch_id,
        #        "compoundId":tRes[0].compound_id,
        #        "boxId":tRes[0].box_id,
        #        "boxDescription":tRes[0].box_description}
        self.finish(json.dumps(res_to_json(tRes, cur)))


@jwtauth
class printBox(tornado.web.RequestHandler):
    def get(self, sBox):
        sSlask = cur.execute("""select box_description, vial_type_desc
                                from vialdb.box b, vialdb.vial_type v
                                where b.vial_type=v.vial_type
                                and box_id = '%s'""" % (sBox))
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
class searchVials(tornado.web.RequestHandler):
    def get(self, sVials):
        sIds = set(sVials.split())
        tmpIds = ""
        jRes = []
        lNotFound = list()
        for sId in sIds:
            sSql = """SELECT b.batch_id as batchId,
                      b.compound_id as compoundId,
                      bbb.box_id as boxId,
                      bbb.box_description as boxDescription,
                      p.coordinate, b.vial_id as vialId,
                      ddd.batch_formula_weight as batchMolWeight,
                      ddd.batch_salt as salt,
                      b.dilution, ddd.cbk_id as cbkId
              FROM
                 vialdb.vial b
                 left outer join vialdb.box_positions p
                 on b.vial_id = p.vial_id
                 left outer join ddd.batch ddd
                 on b.batch_id = ddd.batch_id 
                 left outer join vialdb.box bbb 
                 on bbb.box_id = p.box_id where
                 b.vial_id = '%s'""" % sId
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
                             "coordinate":'',
                             "batchId":'',
                             "compoundId":'',
                             "cbkId":'',
                             "boxId":'Vial not in DB',
                             "batchMolWeight":'',
                             "salt":'',
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
            #                 "salt":row.batch_salt,
            #                 "dilution":row.dilution})
            jRes.append(res_to_json(tRes, cur)[0])
        print(jRes)
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
        if sIds[0].startswith('SLL-'):
            sSql = """
            SELECT b.batch_id as batchId,
            b.compound_id as compoundId,
            bb.cbk_id cbkId,
            bbb.box_id as boxId,
            bbb.box_description as boxDescription,
            p.coordinate,
            b.vial_id vialId,
            bb.batch_formula_weight as batchMolWeight,
            bb.batch_salt as salt
            FROM vialdb.vial b,
            vialdb.box_positions p,
            bcpvs.batch bb, vialdb.box as bbb
            where b.vial_id = p.vial_id and
            bb.batch_id = b.batch_id and bbb.box_id = p.box_id and
	    b.compound_id = %s
            """
        else:
            sSql = """
            SELECT v.batch_id, bb.compound_id, bb.cbk_id,
            bbb.box_description as box_id,
            b.coordinate, v.vial_id,
            batch_formula_weight, batch_salt,
            bb.batch_formula_weight, bb.batch_salt
            FROM
            vialdb.vial v
            inner join bcpvs.batch bb
            on v.batch_id = bb.batch_id
            left join vialdb.box_positions b
            on v.vial_id = b.vial_id
            left join vialdb.box bbb 
            on b.box_id = bbb.box_id
            where v.batch_id = %s
            """
        for sId in sIds:
            sSlask = cur.execute(sSql, sId)
            tRes = cur.fetchall()
            if len(tRes) == 0:
                jRes.append({"vialId":sId,
                             "coordinate":'',
                             "batchId":'',
                             "compoundId":'',
                             "cbkId":'',
                             "boxId":'Not found',
                             "batchMolWeight":'',
                             "salt":''})
                continue
            #for row in tRes:
            #    jRes.append({"vialId":row.vial_id,
            #                 "coordinate":row.coordinate,
            #                 "batchId":row.batch_id,
            #                 "compoundId":row.compound_id,
            #                 "cbkId":row.cbk_id,
            #                 "boxId":row.box_id,
            #                 "batchMolWeight":row.batch_formula_weight,
            #                 "salt":row.batch_salt})
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
class moveVialToLocation(tornado.web.RequestHandler):
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


class StaticFileHandler(tornado.web.StaticFileHandler):
    def get(self, path, include_body=True):
        if path.endswith('woff'):
            self.set_header('Content-Type','application/font-woff')
        super(StaticFileHandler, self).get(path, include_body)


class GetDatabase(tornado.web.RequestHandler):
    def get(self):
        sRes = json.dumps([['Live'], ['Test']])
        self.finish(sRes)

import tornado.gen
import json
import logging
import datetime
import time
import os, random, string
import re
import util
import mydb
import config

db = mydb.disconnectSafeConnect()
cur = db.cursor()

class InitiateDownload(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        random_number = str(random.randint(0, 1000000))
        self.finish(random_number)
        dir_name = f'dist/export/{random_number}'
        os.makedirs(dir_name, exist_ok=True)


class AddMolfileToSdf(tornado.web.RequestHandler):
    def get(self, sTicket, sId):
        sdfile = f'dist/export/{sTicket}/export.sdf'
        elements = sId.split(',')

        # Add single quotes around each element and join them back together
        result_string = ','.join(["'" + element + "'" for element in elements])

        sError = dict()

        sSql = ''
        if sId[:3].upper() == "CBK":
            with open(sdfile, 'a') as file:
                for id in elements:
                    if id =='':
                        continue
                    sSql = f'''
                    select mol, compound_id from bcpvs.JCMOL_MOLTABLE where compound_id = '{id}'
'''
                    cur.execute(sSql)
                    tRes = cur.fetchall()
                    if len(tRes) == 1:
                        sMol = f'''{tRes[0][0]}
> <COMPOUND_ID>
{tRes[0][1]}
$$$$
'''
                        file.write(sMol)
                    else:
                        sError[id] = 'Error'
        else:
            with open(sdfile, 'a') as file:
                for id in elements:
                    if id =='':
                        continue
                    sSql = f'''select mol, m.compound_id, notebook_ref as batch_id from bcpvs.JCMOL_MOLTABLE m, bcpvs.batch b 
where
m.compound_id = b.compound_id and 
notebook_ref = '{id}'
'''
                    cur.execute(sSql)
                    tRes = cur.fetchall()
                    if len(tRes) == 1:
                        sMol = f'''{tRes[0][0]}
> <COMPOUND_ID>
{tRes[0][1]}

> <BATCH_ID>
{tRes[0][2]}
$$$$
'''
                        file.write(sMol)
                    else:
                        sError[id] = 'Error'

        self.finish(json.dumps(sError))

'''
https://esox3.scilifelab.se/vialdb/initiateSdfDownload
https://esox3.scilifelab.se/vialdb/addMolfileToSdf/977775/test
'''

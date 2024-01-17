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
        sdfile = f'dist/export/{sTicket}/t.sdf'
        
        with open(sdfile, 'a') as file:
            # Append the string 'test'
            file.write(f'{sId}\n')

        data = {'id': sId}
        self.finish(json.dumps(data))

'''
https://esox3.scilifelab.se/vialdb/initiateSdfDownload
https://esox3.scilifelab.se/vialdb/addMolfileToSdf/977775/test
'''

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
import zipfile

db = mydb.disconnectSafeConnect()
cur = db.cursor()


def getMolfile(sCmpId):
    sSql = f"""select mol from bcpvs.JCMOL_MOLTABLE where compound_id = '{sCmpId}'"""
    cur.execute(sSql)
    res = cur.fetchall()
    sMol = ''
    if len(res) == 1:
        sMol = f'''{res[0][0]}
> <CIDX>
{sCmpId}

$$$$
'''

    return sMol


class ChemblExport(tornado.web.RequestHandler):
    def get(self, sRIDX, sBatches):
        pass
    def post(self, *args, **kwargs):
        try:
            sRIDX = self.get_argument("RIDX")
            sBatches = self.get_argument("batches")
        except:
            logging.error(f"chembl error")
            return
        saBatches = sBatches.split()
        sMol = ''
        random_number = str(random.randint(0, 1000000))
        dir_name = f'dist/export/{random_number}'
        os.makedirs(dir_name, exist_ok=True)
        file_path = dir_name + "/COMPOUND_RECORD.tsv"
        molfile_path = dir_name + "/COMPOUND_CTAB.sdf"
        with open(file_path, 'w') as file, open(molfile_path, 'w') as molfile_file:
            sHeader = ('CIDX', 'RIDX', 'COMPOUND_NAME', 'COMPOUND_KEY')

            file.write('\t'.join(map(str, sHeader)) + '\n')
            for batch in saBatches:
                sMol = ''
                sSql = f"""select compound_id, "{sRIDX}", notebook_ref, compound_id from bcpvs.batch where notebook_ref = '{batch}'"""
                cur.execute(sSql)
                res = cur.fetchall()
                if len(res) == 1:
                    sMol = getMolfile(res[0][0])
                    file.write('\t'.join(map(str, res[0])) + '\n')
                    molfile_file.write(sMol)

        zip_filepath = os.path.join(dir_name, "COMP.zip")

        with zipfile.ZipFile(zip_filepath, 'w') as zipf:
            zipf.write(os.path.join(dir_name, "COMPOUND_RECORD.tsv"), arcname="COMPOUND_RECORD.tsv")
            zipf.write(os.path.join(dir_name, "COMPOUND_CTAB.sdf"), arcname="COMPOUND_CTAB.sdf")

        

        self.write(json.dumps(f'''<a href=https://esox3.scilifelab.se/vialdb/dist/export/{random_number}/COMP.zip>COMP.zip</a>'''))


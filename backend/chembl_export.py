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

'''
Sample data:
EXP-14-BE7698
Helleday_SAMHD1
AA0763244 AA1963128 AA0340383

Example of ACTIVITY.tsv file:
RIDX	Pathogen_Box_Bloggs	Pathogen_Box_Bloggs	Pathogen_Box_Bloggs
CRIDX	Pathogen_Box_Bloggs	Pathogen_Box_Bloggs	Pathogen_Box_Bloggs
CRIDX_DOCID
CRIDX_CHEMBLID
CIDX	MMV161996	MMV202458	MMV676395
SRC_ID_CIDX
AIDX	1	1	1
TYPE	Inhibition	Inhibition	Inhibition
ACTION_TYPE	ANTAGONIST	ANTAGONIST	ANTAGONIST
TEXT_VALUE
RELATION	=	=	=
VALUE	0	1	61
UPPER_VALUE
UNITS	%	%	%
SD_PLUS
SD_MINUS
ACTIVITY_COMMENT	Not active	Not active	Active
ACT_ID	PB_FECH_MMV161996	PB_FECH_MMV202458	PB_FECH_MMV676395
TEOID



'''


def exportFromBatches(saBatches, sRIDX, compound_record_file, molfile_file):
    for batch in saBatches:
        sMol = ''
        sSql = f"""select compound_id, "{sRIDX}", notebook_ref, compound_id from bcpvs.batch where notebook_ref = '{batch}'"""
        cur.execute(sSql)
        res = cur.fetchall()
        if len(res) == 1:
            sMol = getMolfile(res[0][0])
            compound_record_file.write('\t'.join(map(str, res[0])) + '\n')
            molfile_file.write(sMol)


def exportFromElnProject(sProject, sELN, sRIDX, compound_record_file, molfile_file):
    sSql = f'''select a.compound_id, compound_batch, mol from assay.lcb_sp a, bcpvs.JCMOL_MOLTABLE m
    where a.compound_id = m.compound_id
    and a.project = '{sProject}'
    and a.eln_id = '{sELN}' '''
    cur.execute(sSql)
    res = cur.fetchall()
    for row in res:
        sCmpId = row[0]
        sBatch = row[1]
        sMol = row[2]
        sMolfile = ''
        if len(sMol) > 5:
            sMolfile = f'''{sMol}
> <CIDX>
{sCmpId}

$$$$
'''
            compound_record_file.write(f'''{sCmpId}\t{sRIDX}\t{sBatch}\t{sCmpId}\n''')
            molfile_file.write(sMolfile)
        
            


class ChemblExport(tornado.web.RequestHandler):
    def get(self, sRIDX, sBatches):
        pass
    def post(self, *args, **kwargs):
        try:
            sRIDX = self.get_argument("RIDX").strip()
            sAIDX = self.get_argument("AIDX").strip()
            sProject = self.get_argument("project").strip()
            sELN = self.get_argument("ELN").strip()
            sBatches = self.get_argument("batches").strip()
        except:
            logging.error(f"chembl error")
            return
        if len(sProject) > 2 and len(sELN) > 2:
            sBatches = ''
        saBatches = sBatches.split()
        sMol = ''
        random_number = str(random.randint(0, 1000000))
        dir_name = f'dist/export/{random_number}'
        os.makedirs(dir_name, exist_ok=True)
        file_path = dir_name + "/COMPOUND_RECORD.tsv"
        molfile_path = dir_name + "/COMPOUND_CTAB.sdf"
        
        with open(file_path, 'w') as compound_record_file, open(molfile_path, 'w') as molfile_file:
            sHeader = ('CIDX', 'RIDX', 'COMPOUND_NAME', 'COMPOUND_KEY')

            compound_record_file.write('\t'.join(map(str, sHeader)) + '\n')
            if len(saBatches) > 0:
                exportFromBatches(saBatches, sRIDX, compound_record_file, molfile_file)
            elif len(sProject) > 2 and len(sELN) > 2:
                exportFromElnProject(sProject, sELN, sRIDX, compound_record_file, molfile_file)
            
        zip_filepath = os.path.join(dir_name, "COMP.zip")

        with zipfile.ZipFile(zip_filepath, 'w') as zipf:
            zipf.write(os.path.join(dir_name, "COMPOUND_RECORD.tsv"), arcname="COMPOUND_RECORD.tsv")
            zipf.write(os.path.join(dir_name, "COMPOUND_CTAB.sdf"), arcname="COMPOUND_CTAB.sdf")

        

        self.write(json.dumps(f'''<a href=https://esox3.scilifelab.se/vialdb/dist/export/{random_number}/COMP.zip>COMP.zip</a>'''))


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



def create_ACTIVITY_tsv(tRes,
                        sProject,
                        sELN,
                        sRIDX,
                        sAIDX,
                        sTARGET_TYPE,
                        sASSAY_TYPE,
                        sACTION_TYPE,
                        dir_name):
    '''
RIDX
CRIDX
CRIDX_DOCID
CRIDX_CHEMBLID
CIDX
SRC_ID_CIDX
AIDX
TYPE
ACTION_TYPE
TEXT_VALUE
RELATION
VALUE
UPPER_VALUE
UNITS
SD_PLUS
SD_MINUS
ACTIVITY_COMMENT
ACT_ID
TEOID

tRes columns:
0    compound_id,
1    compound_batch,
2    mol,
3    inhibition,
4    activation,
5    hit_description


    '''
    iDataCol = 3
    sType = 'Inhibition'
    if tRes[0][3] == None and tRes[0][4] != None:
        iDataCol = 4
        sType = 'Activation'

    # sRIDX = 
    sCRIDX = sRIDX
    sCRIDX_DOCID = ''
    sCRIDX_CHEMBLID = ''
    # sCIDX = 
    sSRC_ID_CIDX = ''
    # sAIDX = 
    sTYPE = sType
    sACTION_TYPE = sACTION_TYPE
    sTEXT_VALUE = ''
    sRELATION = '='
    # sVALUE = 
    sUPPER_VALUE = ''
    sUNITS = '%'
    sSD_PLUS = ''
    sSD_MINUS = ''
    # sACTIVITY_COMMENT = 
    sACT_ID = ''
    sTEOID = sELN

        
    activity_tsv_name = dir_name + "/ACTIVITY.tsv"
    with open(activity_tsv_name, 'w') as activity_tsv_file:
        sHeader = (
            'RIDX',
            'CRIDX',
            'CRIDX_DOCID',
            'CRIDX_CHEMBLID',
            'CIDX',
            'SRC_ID_CIDX',
            'AIDX',
            'TYPE',
            'ACTION_TYPE',
            'TEXT_VALUE',
            'RELATION',
            'VALUE',
            'UPPER_VALUE',
            'UNITS',
            'SD_PLUS',
            'SD_MINUS',
            'ACTIVITY_COMMENT',
            'ACT_ID',
            'TEOID')
        activity_tsv_file.write('\t'.join(map(str, sHeader)) + '\n')

        for row in tRes:
            sCIDX = row[0] # COMPOUND_ID
            sValue = row[iDataCol]
            sActivityComment = row[5]
            activity_tsv_file.write(f'''{sRIDX}\t{sCRIDX}\t{sCRIDX_DOCID}\t{sCRIDX_CHEMBLID}\t{sCIDX}\t{sSRC_ID_CIDX}\t{sAIDX}\t{sTYPE}\t{sACTION_TYPE}\t{sTEXT_VALUE}\t{sRELATION}\t{sValue}\t{sUPPER_VALUE}\t{sUNITS}\t{sSD_PLUS}\t{sSD_MINUS}\t{sActivityComment}\t{sACT_ID}\t{sTEOID}\n''')

        
def exportFromElnProject(saCompounds,
                         sProject,
                         sELN,
                         sRIDX,
                         sAIDX,
                         sTARGET_TYPE,
                         sASSAY_TYPE,
                         sACTION_TYPE,
                         compound_record_file,
                         molfile_file,
                         dir_name):
    sComp = ''
    sNotTheseCompounds = ''
    if len(saCompounds) == 1:
        sComp = f''' '{saCompounds[0]}' '''
    elif len(saCompounds) > 1:
        for compound in saCompounds:
            if sComp == '':
                sComp = f''' '{compound}' '''
            else:
                sComp += f''', '{compound}' '''

    if sComp != '':
        sNotTheseCompounds = f''' and a.compound_id not in ({sComp}) '''

    sSql = f'''select
    a.compound_id,
    compound_batch,
    bin2mol( moldepict(mol) ),
    inhibition*100,
    activation*100,
    CASE 
        WHEN hit = 0 THEN 'Not active'
        WHEN hit = 1 THEN 'Active'
    END AS hit_description

    from assay.lcb_sp a, bcpvs.JCMOL_MOLTABLE m
    where a.compound_id = m.compound_id
    and a.project = '{sProject}'
    and a.eln_id = '{sELN}'
    {sNotTheseCompounds}
    order by a.compound_id
    '''
    cur.execute(sSql)
    res = cur.fetchall()
    sPrevCompId = ''
    for row in res:
        sCmpId = row[0]
        sBatch = row[1]
        sMol = row[2]
        sMolfile = ''
        
        if len(sMol) > 5 and sPrevCompId != sCmpId:
            sMolfile = f'''{sMol.decode('utf-8')}
> <CIDX>
{sCmpId}

$$$$
'''
            compound_record_file.write(f'''{sCmpId}\t{sRIDX}\t{sBatch}\t{sCmpId}\n''')
            molfile_file.write(sMolfile)
        sPrevCompId = sCmpId
            
    create_ACTIVITY_tsv(res,
                        sProject,
                        sELN,
                        sRIDX,
                        sAIDX,
                        sTARGET_TYPE,
                        sASSAY_TYPE,
                        sACTION_TYPE,
                        dir_name)


class ChemblExport(tornado.web.RequestHandler):
    def get(self, sRIDX, sBatches):
        pass
    def post(self, *args, **kwargs):
        try:
            sRIDX = self.get_argument("RIDX").strip()
            sAIDX = self.get_argument("AIDX").strip()
            sProject = self.get_argument("project").strip()
            sELN = self.get_argument("ELN").strip()
            sTARGET_TYPE = self.get_argument("TARGET_TYPE").strip()
            sASSAY_TYPE = self.get_argument("ASSAY_TYPE").strip()
            sACTION_TYPE = self.get_argument("ACTION_TYPE").strip()
            sBatches = self.get_argument("batches").strip()
        except:
            logging.error(f"chembl error")
            return
        '''
        if len(sProject) > 2 and len(sELN) > 2:
            sBatches = ''
        '''
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
            if len(saBatches) > 10000000:
                exportFromBatches(saBatches, sRIDX, compound_record_file, molfile_file)
            elif len(sProject) > 2 and len(sELN) > 2:
                saCompounds = saBatches
                exportFromElnProject(saCompounds,
                                     sProject,
                                     sELN,
                                     sRIDX,
                                     sAIDX,
                                     sTARGET_TYPE,
                                     sASSAY_TYPE,
                                     sACTION_TYPE,
                                     compound_record_file,
                                     molfile_file,
                                     dir_name)

        assay_tsv_name = dir_name + "/ASSAY.tsv"
        with open(assay_tsv_name, 'w') as assay_tsv_file:
            sHeader = (
                'AIDX',
                'RIDX',
                'ASSAY_DESCRIPTION',
                'ASSAY_TYPE',
                'ASSAY_ORGANISM',
                'ASSAY_STRAIN',
                'ASSAY_TAX_ID',
                'ASSAY_TISSUE',
                'ASSAY_CELL_TYPE',
                'ASSAY_SUBCELLULAR_FRACTION',
                'ASSAY_SOURCE',
                'TARGET_TYPE',
                'TARGET_NAME',
                'TARGET_ACCESSION',
                'TARGET_ORGANISM',
                'TARGET_TAX_ID')
            # sAIDX =
            # sRIDX =
            sASSAY_DESCRIPTION = ''
            # sASSAY_TYPE =
            sASSAY_ORGANISM = ''
            sASSAY_STRAIN = ''
            sASSAY_TAX_ID = ''
            sASSAY_TISSUE = ''
            sASSAY_CELL_TYPE = ''
            sASSAY_SUBCELLULAR_FRACTION = ''
            sASSAY_SOURCE = ''
            # sTARGET_TYPE = 
            sTARGET_NAME = ''
            sTARGET_ACCESSION = ''
            sTARGET_ORGANISM = ''
            sTARGET_TAX_ID = ''
            assay_tsv_file.write('\t'.join(map(str, sHeader)) + '\n')
            assay_tsv_file.write(f'''{sAIDX}\t{sRIDX}\t{sASSAY_DESCRIPTION}\t{sASSAY_TYPE}\t{sASSAY_ORGANISM}\t{sASSAY_STRAIN}\t{sASSAY_TAX_ID}\t{sASSAY_TISSUE}\t{sASSAY_CELL_TYPE}\t{sASSAY_SUBCELLULAR_FRACTION}\t{sASSAY_SOURCE}\t{sTARGET_TYPE}\t{sTARGET_NAME}\t{sTARGET_ACCESSION}\t{sTARGET_ORGANISM}\t{sTARGET_TAX_ID}\n''')
        

        reference_tsv_name = dir_name + "/REFERENCE.tsv"
        with open(reference_tsv_name, 'w') as reference_tsv_file:
            sHeader = (
                'RIDX',
                'PUBMED_ID',
                'JOURNAL_NAME',
                'YEAR',
                'VOLUME',
                'ISSUE',
                'FIRST_PAGE',
                'LAST_PAGE',
                'REF_TYPE',
                'TITLE',
                'DOI',
                'PATENT_ID',
                'ABSTRACT',
                'AUTHORS')
            reference_tsv_file.write('\t'.join(map(str, sHeader)) + '\n')
            reference_tsv_file.write(f'''{sRIDX}\t\t\t\t\t\t\t\t\t\t\t\t\t\n''')


        assay_param_tsv_name = dir_name + "/ASSAY_PARAM.tsv"
        with open(assay_param_tsv_name, 'w') as assay_param_tsv_file:
            sHeader = (
                'AIDX',
                'TYPE',
                'RELATION',
                'VALUE',
                'UNITS',
                'TEXT_VALUE',
                'COMMENTS')

            assay_param_tsv_file.write('\t'.join(map(str, sHeader)) + '\n')
            assay_param_tsv_file.write(f'''{sAIDX}\t\t\t\t\t\t\n''')

            
        zip_filepath = os.path.join(dir_name, "ChEMBL_deposit.zip")

        with zipfile.ZipFile(zip_filepath, 'w') as zipf:
            zipf.write(os.path.join(dir_name, "COMPOUND_RECORD.tsv"), arcname="COMPOUND_RECORD.tsv")
            zipf.write(os.path.join(dir_name, "COMPOUND_CTAB.sdf"), arcname="COMPOUND_CTAB.sdf")
            zipf.write(os.path.join(dir_name, "ACTIVITY.tsv"), arcname="ACTIVITY.tsv")
            zipf.write(os.path.join(dir_name, "ASSAY.tsv"), arcname="ASSAY.tsv")
            zipf.write(os.path.join(dir_name, "REFERENCE.tsv"), arcname="REFERENCE.tsv")
            zipf.write(os.path.join(dir_name, "ASSAY_PARAM.tsv"), arcname="ASSAY_PARAM.tsv")

        
        self.write(json.dumps(f'''<a href=https://esox3.scilifelab.se/chemreg/dist/export/{random_number}/ChEMBL_deposit.zip>ChEMBL_deposit.zip</a>'''))


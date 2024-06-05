import tornado.autoreload
import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado import web
import util
import os
import application
import exportSdf
import chembl_export
from tornado.options import define, options
import logging
from tornado.log import enable_pretty_logging
import MySQLdb
from datetime import datetime, timedelta
import jwt
import json

# Secret stuff in config file
import config

tornado.log.enable_pretty_logging()
logging.getLogger().setLevel(logging.DEBUG)

root = os.path.dirname(__file__)
settings = {
    "cookie_secret": config.secret_key,
}

JWT_SECRET = config.secret_key
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_SECONDS = 999999

class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        pass
        
    def post(self):
        self.write('some post')

    def get(self):
        self.write('some get')

    def options(self, *args):
        # no body
        # `*args` is for route with `path arguments` supports
        self.set_status(204)
        self.finish()

class login(tornado.web.RequestHandler):
    def post(self, *args):
        username = self.get_argument('username')
        password = self.get_argument('password')
        database = self.get_argument('database')
        try:
            db_connection2 = MySQLdb.connect(
                host="esox3",
                user=username,
                passwd=password
            )
            db_connection2.close()
        except Exception as ex:
            logging.error(str(ex))
            self.set_status(400)
            self.write({'message': 'Wrong username password'})
            self.finish()
            return
        payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
        }
        jwt_token = jwt.encode(payload, JWT_SECRET, JWT_ALGORITHM)
        self.write({'token': jwt_token,
                    'database': database})
        logging.info(f'Login: {username} Database: {database}')

    def get(self):
        pass

class getVersionData(tornado.web.RequestHandler):
    def post(self):
        pass

    def get(self):
        # send verdat

        # tentative
        #os_name = self.get_argument('os_name')
        ## query db for version
        #sSql = f'''select version
        #           from `chem_reg`.`chemreg_dist`
        #           where os = {os_name};
        #        '''
        #cur.execute(sSql)
        #res = cur.fetchall()
        #self.write({"version": f'{res[0][0]}'})

        try:
            with open('./ver.dat', 'r') as f:
                self.write(json.load(f))
                return
        except Exception as e:
            logging.error(str(e))
            self.set_status(500)
            self.write({'message': 'ver.dat not available'})


class getCelloBinary(tornado.web.RequestHandler):
    def post(self):
        pass

    def get(self, os_name):
        # send cello
        #os_name = self.get_argument('os_name')
        # tentative
        
        #
        #if not (os_name == 'Windows' or os_name == 'Linux' or os_name == 'Darwin'):
        #    # unsupported OS
        #    self.set_status(500)
        #    self.write({'message': 'OS not supported'})
        #    return
        #try:
        #    sSql = f'''select program
        #           from chem_reg.chemreg_dist
        #           where os = {os_name};
        #        '''
        #    cur.execute(sSql)
        #    res = cur.fetchall()
        #    logger.info("sending bin file")
        #    self.set_status(200)
        #    self.write(res[0][0])
        #except Exception as e:
        #    logger.error(f"Did not send bin file, error: {str(e)}")

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
        try:
            with open(bin_file, 'rb') as f:
                logging.info("sending bin file")
                self.set_status(200)
                self.write(f.read())
        except Exception as e:
            logging.error(f"Did not send bin file, error: {str(e)}")

           
def make_app():
    return tornado.web.Application([
        (r"/login", login),
        (r"/pingDB", application.PingDB),
        (r"/getVersionData", getVersionData),
        (r"/initiateSdfDownload", exportSdf.InitiateDownload),
        (r"/addMolfileToSdf/(?P<sTicket>[^\/]+)/(?P<sId>[^\/]+)", exportSdf.AddMolfileToSdf),
        (r"/uploadVersionNo", application.UploadVersionNo),
        (r"/getCelloBinary/(?P<os_name>[^\/]+)", getCelloBinary),
        (r"/getDatabase", application.GetDatabase),
        (r"/mols/(.*)", tornado.web.StaticFileHandler, {"path": "mols/"}),
        (r"/dist/(.*)", tornado.web.StaticFileHandler, {"path": "dist/"}),
        (r"/createMolImage/(?P<sId>[^\/]+)", application.CreateMolImage),
        (r"/uploadBinary", application.UploadBinary),
        (r"/uploadLauncher", application.UploadLauncher),
        (r"/uploadTaredVials", application.UploadTaredVials),
        (r"/getLocationPath/(?P<sLocation>[^\/]+)", application.GetLocationPath),
        (r"/getLocationChildren/(?P<sLocation>[^\/]+)", application.GetLocationChildren),
        (r"/getLocationByStorage/(?P<sStorage>[^\/]+)", application.GetLocationByStorage),
        (r"/createEmptyVials/(?P<sNrOfVials>[^\/]+)", application.CreateEmptyVials),
        (r"/addBox/(?P<sParent>[^\/]+)/(?P<sBoxName>[^\/]+)/(?P<sBoxSize>[^\/]+)",
         application.AddBox),
        (r"/addLocation/(?P<sParent>[^\/]+)/(?P<sLocationName>[^\/]+)/(?P<sLocationType>[^\/]+)",
         application.AddLocation),
        (r"/moveBox/(?P<sBox>[^\/]+)/(?P<sLocation>[^\/]+)", application.MoveBox),
        (r"/updateBoxName/(?P<sBox>[^\/]+)/(?P<sNewName>[^\/]+)", application.UpdateBoxName),
        (r"/getBox/(?P<sBox>[^\/]+)", application.GetBox),
        (r"/getBoxLocation/(?P<sBox>[^\/]+)", application.GetBoxLocation),
        (r"/printBox/(?P<sBox>[^\/]+)", application.printBox),
        (r"/printPlate/(?P<sPlate>[^\/]+)", application.PrintPlate),
        (r"/getMicroTubes/(?P<sBatches>[^\/]+)", application.getMicroTubes),
        (r"/getMicroTubesFromFile", application.GetMicroTubesFromFile),
        (r"/getRack/(?P<sRacks>[^\/]+)", application.getRack),
        (r"/printRack/(?P<sRack>[^\/]+)", application.PrintRack),
        (r"/printRackList/(?P<sRack>[^\/]+)", application.PrintRackList),
        (r"/updateRackLocation/(?P<sRack>[^\/]+)/(?P<sLocation>[^\/]+)",
         application.UpdateRackLocation),
        (r"/readScannedRack", application.ReadScannedRack),
        (r"/getFreeBoxes", application.GetFreeBoxes),
        (r"/createPlateFromRack/(?P<sRack>[^\/]+)/(?P<sVolume>[^\/]+)", application.CreatePlateFromRack),
        (r"/duplicatePlate/(?P<sPlate>[^\/]+)/(?P<sVolume>[^\/]+)", application.DuplicatePlate),
        (r"/createPlates/(?P<sPlateType>[^\/]+)/(?P<sPlateName>[^\/]+)/(?P<sNumberOfPlates>[^\/]+)/(?P<sLocation>[^\/]+)/(?P<sDuplicate>[^\/]+)",
         application.CreatePlates),
        (r"/createPlatesFromLabel/(?P<sStartPlate>[^\/]+)/(?P<sPlateType>[^\/]+)/(?P<sPlateName>[^\/]+)/(?P<sNumberOfPlates>[^\/]+)",
         application.CreatePlatesFromLabel),
        (r"/createRacks/(?P<sNumberOfRacks>[^\/]+)", application.CreateRacks),
        (r"/uploadWellInformation", application.UploadWellInformation),
        (r"/uploadAccumulatedRows", application.UploadAccumulatedRows),
        (r"/mergePlates", application.MergePlates),
        (r"/getPlateForPlatemap/(?P<sPlate>[^\/]+)", application.GetPlateForPlatemap),
        (r"/getPlate/(?P<sPlate>[^\/]+)", application.GetPlate),
        (r"/setPlateType/(?P<sPlate>[^\/]+)/(?P<sPlateType>[^\/]+)", application.SetPlateType),
        (r"/verifyPlate/(?P<sPlate>[^\/]+)", application.VerifyPlate),
        (r"/updatePlateName/(?P<sPlate>[^\/]+)/(?P<sPlateName>[^\/]+)/(?P<sPlateLocation>[^\/]+)",
         application.UpdatePlateName),
        (r"/batchInfo/(?P<sBatch>[^\/]+)", application.batchInfo),
        (r"/searchBatches/(?P<vials>[^\/]+)/(?P<tubes>[^\/]+)/(?P<plates>[^\/]+)/(?P<sBatches>[^\/]+)", application.searchBatches),
        (r"/searchVials/(?P<sVials>[^\/]+)", application.searchVials),
        (r"/transitVials/(?P<sVials>[^\/]+)", application.TransitVials),
        (r"/printVial/(?P<sVial>[^\/]+)", application.printVial),
        (r"/discardVial/(?P<sVial>[^\/]+)", application.DiscardVial),
        (r"/discardPlate/(?P<sPlate>[^\/]+)", application.DiscardPlate),
        (r"/verifyLocation/(?P<sLocation>[^\/]+)", application.VerifyLocation),
        (r"/deleteLocation/(?P<sLocation>[^\/]+)", application.DeleteLocation),
        (r"/updateVialPosition/(?P<sVialId>[^\/]+)/(?P<sBoxId>[^\/]+)/(?P<sPos>[^\/]+)",
         application.UpdateVialPosition),
        (r"/editVial", application.EditVial),
        (r"/vialInfo/(?P<sVial>[^\/]+)", application.vialInfo),
        (r"/addMicrotube/(?P<sTubeId>[^\/]+)/(?P<sBatchId>[^\/]+)/(?P<sVolume>[^\/]+)/(?P<sConc>[^\/]*)",
         application.AddMicrotube),
        (r"/listFiles", application.ListDownloadFiles),
        (r"/", application.ListDownloadFiles),
        (r"/verifyVial/(?P<sVial>[^\/]+)", application.verifyVial),
        (r"/getCelloLauncher/Windows/(.*)", web.StaticFileHandler, {"path": "dist/launchers/Windows/"}),
        (r"/getCelloLauncher/Linux/(.*)", web.StaticFileHandler, {"path": "dist/launchers/Linux/"}),
        (r"/getCelloLauncher/Darwin/(.*)", web.StaticFileHandler, {"path": "dist/launchers/Darwin/"}),
        (r"/chemblExport/(?P<sRIDX>[^\/]+)/(?P<project>[^\/]+)/(?P<ELN>[^\/]+)/(?P<sBatches>[^\/]+)", chembl_export.ChemblExport),
        (r"/chemblExport", chembl_export.ChemblExport),
        (r"/(.*)", web.StaticFileHandler,  {"path": "dist", "default_filename": "index.html"}),
        (r'.*', util.BaseHandler),
    ], **settings)

if __name__ == "__main__":
    app = make_app()
    app.listen(8082, max_buffer_size=200000000)
    tornado.autoreload.start()
    
    for dir, _, files in os.walk('static'):
        [tornado.autoreload.watch(dir + '/' + f) \
         for f in files if not f.startswith('.')]

    tornado.ioloop.IOLoop.current().start()


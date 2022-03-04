import tornado.autoreload
import tornado.httpserver
import tornado.ioloop
import tornado.web
import util
import os
import application
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
JWT_EXP_DELTA_SECONDS = 99999

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
        (r"/getVersionData", getVersionData),
        (r"/getCelloBinary/(?P<os_name>[^\/]+)", getCelloBinary),
        (r"/getDatabase", application.GetDatabase),
        (r"/", application.home),
        (r"/mols/(.*)", tornado.web.StaticFileHandler, {"path": "mols/"}),
        (r"/dist/(.*)", tornado.web.StaticFileHandler, {"path": "dist/"}),
        (r"/createMolImage/(?P<sId>[^\/]+)", application.CreateMolImage),
        (r"/uploadBinary", application.UploadBinary),
        (r"/uploadEmptyVials", application.uploadEmptyVials),
        (r"/getLocations", application.getLocations),
        (r"/getLocationPath/(?P<sLocation>[^\/]+)", application.GetLocationPath),
        (r"/getLocationChildren/(?P<sLocation>[^\/]+)", application.GetLocationChildren),
        (r"/getLocationByStorage/(?P<sStorage>[^\/]+)", application.GetLocationByStorage),
        (r"/createManyVialsNLabels", application.createManyVialsNLabels),
        (r"/addBox/(?P<sParent>[^\/]+)/(?P<sBoxName>[^\/]+)/(?P<sBoxSize>[^\/]+)",
         application.AddBox),
        (r"/addLocation/(?P<sParent>[^\/]+)/(?P<sLocationName>[^\/]+)/(?P<sLocationType>[^\/]+)",
         application.AddLocation),
        (r"/getBox/(?P<sBox>[^\/]+)", application.GetBox),
        (r"/getBoxOfType/(?P<sBoxType>[^\/]+)", application.getBoxOfType),
        (r"/getBoxLocation/(?P<sBox>[^\/]+)", application.GetBoxLocation),
        (r"/getFirstEmptyCoordForBox/(?P<sBox>[^\/]+)", application.getFirstEmptyCoordForBox),
        (r"/printBox/(?P<sBox>[^\/]+)", application.printBox),
        (r"/getMicroTubes/(?P<sBatches>[^\/]+)", application.getMicroTubes),
        (r"/getRack/(?P<sRacks>[^\/]+)", application.getRack),
        (r"/readScannedRack", application.ReadScannedRack),
        (r"/updateBox/(?P<sBox>[^\/]+)", application.updateBox),
        (r"/createLocation", application.createLocation),
        (r"/getFreeBoxes", application.GetFreeBoxes),
        (r"/searchLocation/(?P<sLocation>[^\/]+)", application.searchLocation),
        (r"/batchInfo/(?P<sBatch>[^\/]+)", application.batchInfo),
        (r"/searchBatches/(?P<sBatches>[^\/]+)", application.searchBatches),
        (r"/searchVials/(?P<sVials>[^\/]+)", application.searchVials),
        (r"/transitVials/(?P<sVials>[^\/]+)", application.TransitVials),
        (r"/printVial/(?P<sVial>[^\/]+)", application.printVial),
        (r"/discardVial/(?P<sVial>[^\/]+)", application.discardVial),
        (r"/getLocation", application.getLocation),
        (r"/deleteLocation/(?P<sLocation>[^\/]+)", application.DeleteLocation),
        (r"/moveVialToLocation/(?P<sVial>[^\/]+)/(?P<sUser>[^\/]+)",
         application.MoveVialToLocation),
        (r"/updateVialPosition/(?P<sVialId>[^\/]+)/(?P<sBoxId>[^\/]+)/(?P<sPos>[^\/]+)",
         application.UpdateVialPosition),
        (r"/editVial", application.EditVial),
        (r"/generateVialId", application.generateVialId),
        (r"/vialInfo/(?P<sVial>[^\/]+)", application.vialInfo),
        (r"/addMicrotube/(?P<sTubeId>[^\/]+)/(?P<sBatchId>[^\/]+)/(?P<sVolume>[^\/]+)/(?P<sConc>[^\/]*)",
         application.AddMicrotube),
        (r"/verifyVial/(?P<sVial>[^\/]+)", application.verifyVial),
        (r"/getVialTypes", application.getVialTypes),
        (r"/createBox", application.createBox),
        (r'.*', util.BaseHandler),
    ], **settings)

if __name__ == "__main__":
    app = make_app()
    app.listen(8084)
    tornado.autoreload.start()
    
    for dir, _, files in os.walk('static'):
        [tornado.autoreload.watch(dir + '/' + f) \
         for f in files if not f.startswith('.')]

    tornado.ioloop.IOLoop.current().start()

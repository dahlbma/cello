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


def make_app():
    return tornado.web.Application([
        (r"/login", login),
        (r"/getDatabase", application.GetDatabase),
        (r"/", application.home),
        (r"/mols/(.*)", tornado.web.StaticFileHandler, {"path": "mols/"}),
        ("/login",util.LoginHandler),
        ("/logout", util.LogoutHandler),
        ("/unauthorized", util.UnAuthorizedHandler),
        (r"/createMolImage", application.CreateMolImage),
        (r"/uploadEmptyVials", application.uploadEmptyVials),
        (r"/getLocations", application.getLocations),
        (r"/getLocationByStorage/(?P<sStorage>[^\/]+)", application.GetLocationByStorage),
        (r"/createManyVialsNLabels", application.createManyVialsNLabels),
        (r"/addBox/(?P<sParent>[^\/]+)/(?P<sBoxName>[^\/]+)/(?P<sBoxSize>[^\/]+)", application.AddBox),
        (r"/getBox/(?P<sBox>[^\/]+)", application.GetBox),
        (r"/getBoxOfType/(?P<sBoxType>[^\/]+)", application.getBoxOfType),
        (r"/getBoxLocation/(?P<sBox>[^\/]+)", application.GetBoxLocation),
        (r"/getFirstEmptyCoordForBox/(?P<sBox>[^\/]+)", application.getFirstEmptyCoordForBox),
        (r"/printBox/(?P<sBox>[^\/]+)", application.printBox),
        (r"/getMicroTubeByBatch/(?P<sBatches>[^\/]+)", application.getMicroTubeByBatch),
        (r"/getRack/(?P<sRack>[^\/]+)", application.getRack),
        (r"/readScannedRack", application.readScannedRack),
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
        (r"/moveVialToLocation/(?P<sVial>[^\/]+)/(?P<sUser>[^\/]+)",
         application.MoveVialToLocation),
        (r"/updateVialPosition/(?P<sVialId>[^\/]+)/(?P<sBoxId>[^\/]+)/(?P<sPos>[^\/]+)",
         application.UpdateVialPosition),
        (r"/editVial", application.editVial),
        (r"/generateVialId", application.generateVialId),
        (r"/vialInfo/(?P<sVial>[^\/]+)", application.vialInfo),
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

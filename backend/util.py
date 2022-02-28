import tornado.web
import tornado.auth
import json
import requests
import os
import time
import MySQLdb
from datetime import datetime

from datetime import datetime, timedelta
import logging
import jwt
from auth import jwtauth

# secret stuff
import config

db = MySQLdb.connect(
    host=config.database['host'],
    user=config.database['user'],
    passwd=config.database['password'],
    database=config.database['db']
)

JWT_SECRET = config.secret_key
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_SECONDS = 99999


def isAuthorized(email):
    tRes = db.query("""select user_name, full_name, organization
                       from vialdb.users where email = '%s'""" % (email))
    if len(tRes)>0:
        return True, tRes[0]
    else:
        return False, None

class BaseHandler(tornado.web.RequestHandler):
    """Base Handler. Handlers should not inherit from this
    class directly but from either SafeHandler or UnsafeHandler
    to make security status explicit.
    """
    def get(self):
        """ The GET method on this handler will be overwritten by all other handler.
        As it is the default handler used to match any request that is not mapped
        in the main app, a 404 error will be raised in that case (because the get method
        won't be overwritten in that case)
        """
        raise tornado.web.HTTPError(404, reason='Page not found')

    def get_current_user(self):
        return self.get_secure_cookie("token")

    def get_current_user_name(self):
        # Fix ridiculous bug with quotation marks showing on the web
        #user = self.get_current_user()
        #if user:
        #    if (user[0] == '"') and (user[-1] == '"'):
        #        return user[1:-1]
        #    else:
        #        return user
        
        return self.get_cookie("username")#user

    def write_error(self, status_code, **kwargs):
        """ Overwrites write_error method to have custom error pages.
        http://tornado.readthedocs.org/en/latest/web.html#tornado.web.RequestHandler.write_error
        """
        reason = 'Page not found'
        logging.error(reason)


class SafeHandler(BaseHandler):
    """ All handlers that need authentication and authorization should inherit
    from this class.
    """
    @tornado.web.authenticated
    def prepare(self):
        """This method is called before any other method.
        Having the decorator @tornado.web.authenticated here implies that all
        the Handlers that inherit from this one are going to require
        authentication in all their methods.
        """
        pass

class UnsafeHandler(BaseHandler):
    pass
    

class UnAuthorizedHandler(UnsafeHandler):
    """ Serves a page with unauthorized notice and information about who to contact to get access. """
    def get(self):
        # The parameters email and name can contain anything,
        # be careful not to evaluate them as code
        email = self.get_argument("email", '')
        name = self.get_argument("name", '')
        self.write(contact)

class MainHandler(UnsafeHandler):
    """ Serves the html front page upon request.
    """
    def get(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.write(t.generate(user_name=self.get_current_user_name()))


class SafeStaticFileHandler(tornado.web.StaticFileHandler, SafeHandler):
    """ Serve static files for authenticated users
    """
    pass

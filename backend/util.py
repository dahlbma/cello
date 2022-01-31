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
        print("Error do something here")

class GoogleUser(object):
    """Stores the information that google returns from a user throuhgh its secured API.
    """
    def __init__(self, user_token):

        self.user_token = user_token
        self._google_plus_api = "https://www.googleapis.com/plus/v1/people/me"

        #Fetch actual information from Google API
        params = {'access_token': self.user_token.get('access_token')}
        r = requests.get(self._google_plus_api, params=params)
        if not r.status_code == requests.status_codes.codes.OK:
            self.authenticated = False
        else:
            self.authenticated = True
            info = json.loads(r.text)
            self.display_name = info.get('displayName', '')
            self.emails = [email['value'] for email in info.get('emails')]

    def is_authorized(self, user_view):
        """Checks that the user is actually authorised to use genomics-status.
        """
        authenticated = False
        for email in self.emails:
            if user_view[email]:
                self.valid_email = email
                authenticated = True
        return authenticated

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

class LoginHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    
    def get(self):
        self.write(
            '<form class="modal-content animate" action="/login" method="post">'
                '<div class="container">'
                    '<label for="username"><b>Username</b></label>'
                    '<input type="text" placeholder="Enter Username" name="username" required>'
            
                    '<label for="password"><b>Password</b></label>'
                    '<input type="password" placeholder="Enter Password" name="password" required>'

                    '<button type="submit">Login</button>'
                '</div>'
            '</form>')
        return
        if self.get_argument("code", False):
            user_token =  yield self.get_authenticated_user(
                redirect_uri=self.application.settings['redirect_uri'],
                code=self.get_argument('code')
                )
            user = GoogleUser(user_token)
            #print user.display_name
            #print user.emails
            
            (lAuthorized, saUser) = isAuthorized(user.emails[0])
            if user.authenticated and lAuthorized:
                self.set_secure_cookie('user', user.display_name)
                #It will have at least one email (otherwise she couldn't log in)
                self.set_secure_cookie('email', user.emails[0])
                url=self.get_secure_cookie("login_redirect")
                self.clear_cookie("login_redirect")
                if url is None:
                    url = '/'
            else:
                url = "/unauthorized?email={0}&contact={1}".format(user.emails[0],
                        self.application.settings['contact_person'])
            self.redirect(url)

        else:
            self.set_secure_cookie('login_redirect', self.get_argument("next", '/'), 1)
            self.authorize_redirect(
                        redirect_uri=self.application.settings['redirect_uri'],
                        client_id=self.application.oauth_key,
                        scope=['profile', 'email'],
                        response_type='code',
                        extra_params={'approval_prompt': 'auto'})

    def post(self, *args):
        username = self.get_argument('username')
        password = self.get_argument('password')
        try:
            db_connection2 = MySQLdb.connect(
                host="esox3",
                user=username,
                passwd=password
            )
            db_connection2.close()
        except Exception as ex:
            logging.getLogger().error(str(ex))
            #self.set_status(400)
            #self.write({'message': 'Wrong username password'})
            #self.finish()
            url = "/unauthorized?email={0}&contact={1}".format(username,
                        self.application.settings['contact_person'])
            self.redirect(url)
            return
        payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
        }
        jwt_token = jwt.encode(payload, JWT_SECRET, JWT_ALGORITHM)
        print(username)
        self.set_cookie('username', username)
        self.set_secure_cookie('token', jwt_token)
    
        #self.set_secure_cookie('login_redirect', self.get_argument("next", '/'), 1)
        self.redirect("/")
        #self.authorize_redirect(
        #            redirect_uri=self.application.settings['redirect_uri'],
        #            client_id=self.application.oauth_key,
        #            scope=['profile', 'email'],
        #            response_type='code',
        #            extra_params={'approval_prompt': 'auto'})

    

class LogoutHandler(tornado.web.RequestHandler, tornado.auth.GoogleOAuth2Mixin):
    def get(self):
        self.clear_cookie("user")
        self.clear_cookie("email")
        
        self.clear_cookie("token")
        self.clear_cookie("username")
        self.redirect("/")

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

import tornado.web
import logging


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


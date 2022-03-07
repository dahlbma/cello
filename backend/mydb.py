import MySQLdb 
import config
import logging

class DisconnectSafeCursor(object):
    db = None
    cursor = None

    def __init__(self, db, cursor):
        self.db = db
        self.cursor = cursor

    def close(self):
        self.cursor.close()

    def execute(self, *args, **kwargs):
        try:
            return self.cursor.execute(*args, **kwargs)
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            logging.error(*args)
            e = str(e)
            logging.error(e)
            if '4031' in e:
                logging.info('Reconnecting to database')
                self.db.reconnect()
                self.cursor = self.db.cursor()
                return self.cursor.execute(*args, **kwargs)
            raise Exception(e)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def description(self):
        return self.cursor.description

class DisconnectSafeConnection(object):
    connect_args = None
    connect_kwargs = None
    conn = None

    def __init__(self, *args, **kwargs):
        self.connect_args = args
        self.connect_kwargs = kwargs
        self.reconnect()

    def reconnect(self):
        self.conn = MySQLdb.connect(
            host=config.database['host'],
            user=config.database['user'],
            passwd=config.database['password'],
            database=config.database['db']
        )
        self.conn.autocommit(True)

    def cursor(self, *args, **kwargs):
        cur = self.conn.cursor(*args, **kwargs)
        #sSql = 'set global wait_timeout = 99000'
        #sSql = 'set global interactive_timeout = 99000'
        #cur.execute(sSql)
        return DisconnectSafeCursor(self, cur)

disconnectSafeConnect = DisconnectSafeConnection

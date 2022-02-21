import MySQLdb 
import config


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
        except MySQLdb.OperationalError:
            self.db.reconnect()
            self.cursor = self.db.cursor()
            return self.cursor.execute(*args, **kwargs)

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
        
        return DisconnectSafeCursor(self, cur)


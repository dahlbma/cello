import pymysql 
import config
import logging

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')


def setup_logger(name, log_file, level=logging.INFO):
    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

scarabLogger = setup_logger('scara_logger', 'scarabSqlError.txt')

class DisconnectSafeCursor(object):
    db = None
    cursor = None
    #scarabCursor = None

    def __init__(self, db, cursor):
        self.db = db
        self.cursor = cursor
        #self.scarabCursor = db.scarabCur

    def close(self):
        self.cursor.close()
        #self.scarabCursor.close()

    def ping(self, *args, **kwargs):
        ret = ''
        self.cursor.execute(*args, **kwargs)

        return ret

    def execute(self, *args, **kwargs):
        try:
            return self.cursor.execute(*args, **kwargs)
        except pymysql.OperationalError:
            logging.error(args[0])
            #self.db.reconnect()
            #self.cursor = self.db.cursor()
            #return self.cursor.execute(*args, **kwargs)
            pass

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
    cur = None
    
    def __init__(self, *args, **kwargs):
        self.connect_args = args
        self.connect_kwargs = kwargs
        self.reconnect()

    def reconnect(self):
        self.conn = pymysql.connect(
            host=config.database['host'],
            user=config.database['user'],
            password=config.database['password'],
            database=config.database['db'],
            charset='utf8mb4',
            autocommit=True
        )

        '''
        self.scarabConn = pymysql.connect(
            host=config.scarabDatabase['host'],
            user=config.scarabDatabase['user'],
            password=config.scarabDatabase['password'],
            database=config.scarabDatabase['db'],
            charset='utf8mb4',
            autocommit=True
        )
        '''

    def cursor(self, *args, **kwargs):
        self.cur = self.conn.cursor(*args, **kwargs)
        #self.scarabCur = self.scarabConn.cursor(*args, **kwargs)
        return DisconnectSafeCursor(self, self.cur)

    def commit(self):
        #self.scarabConn.commit()
        self.conn.commit()

    def rollback(self):
        #self.scarabConn.rollback()
        self.conn.rollback()

disconnectSafeConnect = DisconnectSafeConnection

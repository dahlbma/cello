import sys, os, importlib
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import QtGui
from cellolib import *
from loginscreen import LoginScreen

os_name = platform.system()
exec_path = ""
if os_name == 'Windows':
    #windows stuff
    import ctypes
    myappid = 'cello.vial.microtubes'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


def error_handler(etype, value, tb):
    err_msg = "".join(traceback.format_exception(etype, value, tb))
    logging.getLogger().error(f"\n{err_msg}")

#reroute excepthook to custom error_handler
sys.excepthook = error_handler

#base settings for logging
level=logging.INFO

#init root logger
logger = logging.getLogger()
logger.setLevel(level)

#console logging
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)s:%(message)s')
ch.setFormatter(formatter)

#file logging
file=os.path.join(".","cello.log")
fh = logging.FileHandler(file)
fh.setLevel(level)
formatter = logging.Formatter('%(asctime)s : %(name)s:%(levelname)s: %(filename)s:%(lineno)d: %(message)s',
                              datefmt='%m/%d/%Y %H:%M:%S')
fh.setFormatter(formatter)
#output formatting
logger.addHandler(ch)
logger.addHandler(fh)


v_path = os.path.join(".", "ver.dat")
version = ""
if os.path.exists(v_path):
    with open(v_path) as f:
        try:
            js = json.load(f)
            version = js['version']
        except:
            logging.getLogger().error(f"bad json in ./ver.dat")

#base app settings
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "2"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
app = QApplication(['Cello'])
clipboard = app.clipboard()

app.setApplicationName(f"Cello")
welcome = LoginScreen(f'Cello {version}')
widget = QtWidgets.QStackedWidget()
widget.addWidget(welcome)

#window sizing stuff
desktop = QApplication.desktop()
windowHeight = 800
windowWidth = 1200

windowHeight = int(round(0.9 * desktop.screenGeometry().height(), -1))
if windowHeight > 800:
    windowHeight = 800

windowWidth = int(round((1200/800) * windowHeight, -1))

widget.resize(windowWidth, windowHeight)

#Close splash screen
if '_PYIBoot_SPLASH' in os.environ and importlib.util.find_spec("pyi_splash"):
    import pyi_splash
    pyi_splash.close()

#show app
widget.show()
app.setWindowIcon(QtGui.QIcon(resource_path('assets/cello.ico')))
widget.setWindowIcon(QtGui.QIcon(resource_path('assets/cello.ico')))
sys.exit(app.exec_())

import sys, os, importlib
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import QtGui
from cellolib import *
from loginscreen import LoginScreen
import datetime

#setup
os_name = platform.system()
exec_path = ""
if os_name == 'Windows':
    #windows stuff
    import ctypes
    myappid = 'cello.vial.microtubes'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

#init error handler
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
current_datetime = datetime.datetime.now()
formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
file=os.path.join(".",f"cello_{formatted_datetime}.log")
fh = logging.FileHandler(file)
fh.setLevel(level)
formatter = logging.Formatter('%(asctime)s : %(name)s:%(levelname)s: %(filename)s:%(lineno)d: %(message)s',
                              datefmt='%m/%d/%Y %H:%M:%S')
fh.setFormatter(formatter)
#output formatting
logger.addHandler(ch)
logger.addHandler(fh)



# Loop through the handlers to find the FileHandler and get its filename (path)
for handler in logger.handlers:
    if isinstance(handler, logging.FileHandler):
        log_file_path = handler.baseFilename
        log_directory = os.path.dirname(log_file_path)


####################################################################
### Delete old log-files
directory_path = log_directory

# Get the current date and time
current_datetime = datetime.datetime.now()
# Calculate the time threshold (3 days ago)
threshold_datetime = current_datetime - datetime.timedelta(days=3)
# List all files in the directory
file_list = os.listdir(directory_path)

# Iterate through the files and delete .log files older than 3 days
for file_name in file_list:
    file_path = os.path.join(directory_path, file_name)
    
    # Check if the file has a .log extension and if it's older than 3 days
    if file_name.endswith(".log") and datetime.datetime.fromtimestamp(os.path.getctime(file_path)) < threshold_datetime:
        try:
            logging.getLogger().info(f"Deleting: {file_name}")
            os.remove(file_path)
        except Exception as e:
            print(f"Error deleting {file_name}: {str(e)}")
###
####################################################################

#get app version
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
os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1"
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

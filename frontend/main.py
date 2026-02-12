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

def check_launcher_update(launcher_ver_path):
    try:
        r = dbInterface.getVersion()
        if r.status_code != 200:
            logging.getLogger().info("Launcher update check skipped: server error")
            return
        server_info = json.loads(r.content)
    except Exception as e:
        logging.getLogger().info(f"Launcher update check skipped: {e}")
        return

    if not isinstance(server_info, dict):
        return

    server_launcher = server_info.get('launcher_version')
    if not server_launcher:
        return

    local_launcher = None
    try:
        if os.path.exists(launcher_ver_path):
            with open(launcher_ver_path) as f:
                local_info = json.load(f)
                if isinstance(local_info, dict):
                    local_launcher = local_info.get('launcher_version')
    except Exception as e:
        logging.getLogger().info(f"Launcher version read failed: {e}")

    if local_launcher == server_launcher:
        return

    os_name = platform.system()
    exec_name = 'cello.exe' if os_name == 'Windows' else 'cello'
    exec_path = os.path.join(os.getcwd(), exec_name)
    tmp_path = exec_path + '.tmp'

    try:
        bin_r = dbInterface.getLauncherBinary(os_name)
        if bin_r.status_code != 200:
            logging.getLogger().info(f"Launcher download failed with {bin_r.status_code}")
            return
        with open(tmp_path, 'wb') as f:
            for chunk in bin_r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        if os_name != 'Windows':
            os.chmod(tmp_path, 0o775)
        os.replace(tmp_path, exec_path)

        updated_ver_data = {'launcher_version': server_launcher}
        with open(launcher_ver_path, 'w', encoding='utf-8') as ver_file:
            json.dump(updated_ver_data, ver_file, ensure_ascii=False, indent=4)
        logging.getLogger().info(f"Launcher updated to {server_launcher}")
    except Exception as e:
        logging.getLogger().error(f"Launcher update failed: {e}")
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

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
local_ver_data = {}
if os.path.exists(v_path):
    with open(v_path) as f:
        try:
            js = json.load(f)
            version = js['version']
            local_ver_data = js
        except:
            logging.getLogger().error(f"bad json in ./ver.dat")

launcher_ver_path = os.path.join(".", "launcher.ver")
check_launcher_update(launcher_ver_path)

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

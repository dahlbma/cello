import sys, os, logging, traceback
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow
from PyQt5 import QtGui

from cellolib import *

ex_paths = {'Windows': 'ce.exe',
            'Linux':'ce',
            'Darwin':'ce'}

def error_handler(etype, value, tb):
    err_msg = "".join(traceback.format_exception(etype, value, tb))
    logger.exception(err_msg)

class LauncherScreen(QDialog):
    def __init__(self):
        super(LauncherScreen, self).__init__()
        self.mod_name = "launcher"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/launcher.ui"), self)
        self.update_cello_btn.clicked.connect(self.updatefunction)
        self.update_cello_btn.setDefault(False)
        self.update_cello_btn.setAutoDefault(False)
        self.run_cello_btn.clicked.connect(self.runfunction)
        self.run_cello_btn.setDefault(True)
        self.run_cello_btn.setAutoDefault(True)

        if self.ver_check() == 1: #outdated
            self.status_lab.setText("""Cello is outdated!<br>
            Please <b>'Update Cello'</b> or<br>
            <b>'Run Cello'</b> to Update.""")


    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            self.runfunction()
        elif event.key() == QtCore.Qt.Key_R: 
            self.updatefunction()

    def ver_check(self):
        #return true if cello is outdated
        try:
            r = dbInterface.getVersion()
            #turn it into a dict
            info = json.loads(r.content)
            logger.info(f"recieved {info}")
        except Exception as e:
            self.status_lab.setText("ERROR no connection")
            logging.getLogger(self.mod_name).error(str(e))
            return 2, None
        if r.status_code == 500:
            return 2, info
        info_dict = dict()
        try:
            with open('./ver.dat', 'r') as f:
                info_dict = json.load(f)
        except Exception as e:
            logger.error(str(e))
            #create version file
            return 1, {"version":"-1"}
        #check if versions match
        ok = 0 if info['version'] == info_dict['version'] else 1
        #ok is 0 if versions match, 1 if update is needed, 2 if no connection
        return ok, info


    def updatefunction(self):
        os_name = platform.system()
        exec_path = f"{os.getcwd()}/{ex_paths[os_name]}"
        #check if versions match
        match, info = self.ver_check()
        if self.frc_update_chb.isChecked() or not os.path.isfile(exec_path):
            logging.getLogger(self.mod_name).info("Force update")
            match = 1
        if match == 2:
            #no connection to server
            return -1
        elif match == 1:
            #update needed
            # send notification
            send_msg('Updated Version', f"New version information:\n{info['notes']}")
            try: 
                bin_r = dbInterface.getCelloBinary(os_name)
                
                with open(exec_path, 'wb') as cello_file:
                    shutil.copyfileobj(bin_r.raw, cello_file)
                    logging.info("Updated Cello")
                
                os.chmod(exec_path, 0o775)
  
            except Exception as e:
                self.status_lab.setText("ERROR ")
                logging.getLogger(self.mod_name).info(str(e))
                return -1
        #all is well
        try:
            r = dbInterface.getVersion()
            #turn it into a dict
            info = json.loads(r.content)
            logging.getLogger(self.mod_name).info(f"recieved {info}")
        except Exception as e:
            self.status_lab.setText("ERROR no connection")
            logging.getLogger(self.mod_name).error(str(e))
        with open('./ver.dat', 'w', encoding='utf-8') as ver_file:
            json.dump(info, ver_file, ensure_ascii=False, indent=4)
        return 0


    def runfunction(self):
        check = self.updatefunction()
        if check != -1:
            os_name = platform.system()
            exec_path = ex_paths[os_name]
            if os_name == 'Windows':
                subprocess.Popen([f'{exec_path}'], shell=True)
            elif os_name == 'Linux':
                subprocess.Popen([f'./{exec_path}'], shell=True)
            elif os_name == 'Darwin':
                subprocess.Popen(['open', f'{exec_path}'], shell=True)
            else:
                send_msg("Error", "Can not launch Cello, unknown OS", icon=QMessageBox.Warning)
            QtWidgets.QApplication.instance().quit()
        return
        

#base settings for logging
level=logging.INFO

#init root logger
logger = logging.getLogger()
logger.setLevel(level)

#console logging
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)s:%(filename)s:%(lineno)d:%(message)s')
ch.setFormatter(formatter)

#file logging
file=os.path.join(".","cello_launcher.log")
fh = logging.FileHandler(file)
fh.setLevel(level)
formatter = logging.Formatter('%(asctime)s : %(name)s:%(levelname)s: %(filename)s:%(lineno)d: %(message)s',
                              datefmt='%m/%d/%Y %H:%M:%S')
fh.setFormatter(formatter)

logger.addHandler(ch)
logger.addHandler(fh)


#base app settings
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "2"
app = QApplication(['Cello Launcher'])
clipboard = app.clipboard()

launch = LauncherScreen()
widget = QtWidgets.QStackedWidget()
widget.addWidget(launch)

#window sizing stuff
desktop = QApplication.desktop()
windowHeight = 340
windowWidth = 508

#windowHeight = int(round(0.5 * desktop.screenGeometry().height(), -1))
#if windowHeight > 800:
#    windowHeight = 800

#windowWidth = int(round((1200/800) * windowHeight, -1))

widget.resize(windowWidth, windowHeight)

widget.show()
app.setWindowIcon(QtGui.QIcon('asssets/chem.ico'))
widget.setWindowIcon(QtGui.QIcon('assets/chem.ico'))
sys.exit(app.exec_())
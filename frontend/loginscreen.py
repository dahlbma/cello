import sys, requests, logging
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QMessageBox

from cellolib import *
from searchscreen import SearchScreen
from vialsscreen import VialsScreen
from boxesscreen import BoxesScreen
from microtubesscreen import MicrotubesScreen
from platesscreen import PlatesScreen

class LoginScreen(QMainWindow):
    def __init__(self):
        super(LoginScreen, self).__init__()
        self.mod_name = "login"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/welcomescreen.ui"), self)
        self.login.clicked.connect(self.loginfunction)
        saDatabases = None
        try:
            saDatabases = dbInterface.getDatabase()
        except Exception as e:
            send_msg("Connection Error", f"Cello has encountered a fatal error:\n\n{str(e)}\n\nPlease restart Cello.", icon=QMessageBox.Critical, e=e)
            sys.exit()
        self.server_cb.addItems(saDatabases)
    
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            self.loginfunction()
    
    def loginfunction(self):
        
        user = self.usernamefield.text()
        password = self.passwordfield.text()
        database = self.server_cb.currentText()
        if len(user) == 0 or len(password) == 0:
            self.errorlabel.setText("Please input all fields")
        else:
            self.errorlabel.setText("")
        
        try:
            r = dbInterface.login(user, password, database)
        except Exception as e:
            self.errorlabel.setText("Bad Connection")
            send_msg("Error Message", str(e), QMessageBox.Warning, e)
            logging.getLogger(self.mod_name).error(str(e))
            return
        if r.status_code != 200:
            self.errorlabel.setText("Wrong username/password")
            return
        self.jwt_token = r.content
        self.startApp(database)

    def startApp(self, db):
        test = 'false'
        if db != 'Live':
            test = 'true'

        app = QtCore.QCoreApplication.instance()
        self.window().setWindowTitle(f"{app.applicationName()} {db}")

        #init
        search = SearchScreen(self.jwt_token, test)
        vials = VialsScreen(self.jwt_token, test)
        boxes = BoxesScreen(self.jwt_token, test)
        microtubes = MicrotubesScreen(self.jwt_token, test)
        plates = PlatesScreen(self.jwt_token, test)

        #add screens to stackedwidget
        self.window().addWidget(search)
        self.window().addWidget(vials)
        self.window().addWidget(boxes)
        self.window().addWidget(microtubes)
        self.window().addWidget(plates)

        #first screen
        gotoSearch(self)
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

class LoginScreen(QMainWindow):
    def __init__(self):
        super(LoginScreen, self).__init__()
        self.mod_name = "login"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/welcomescreen.ui"), self)
        #self.passwordfield.setEchoMode(QtWidgets.QLineEdit.Password)
        self.login.clicked.connect(self.loginfunction)
        saDatabases = dbInterface.getDatabase()
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
        self.startApp()

    def startApp(self):
        # init
        search = SearchScreen(self.jwt_token)
        vials = VialsScreen(self.jwt_token)
        boxes = BoxesScreen(self.jwt_token)
        microtubes = MicrotubesScreen(self.jwt_token)

        # add screens to stackedwidget
        self.window().addWidget(search)
        self.window().addWidget(vials)
        self.window().addWidget(boxes)
        self.window().addWidget(microtubes)
        #gotoSearch(self)
        gotoBoxes(self)
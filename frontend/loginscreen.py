import sys, requests, logging
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QMessageBox

from cellolib import *


class LoginScreen(QMainWindow):
    def __init__(self):
        super(LoginScreen, self).__init__()
        self.mod_name = "login"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/welcomescreen.ui"), self)
        #self.passwordfield.setEchoMode(QtWidgets.QLineEdit.Password)
        self.login.clicked.connect(self.loginfunction)
    
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            self.loginfunction()
    
    def loginfunction(self):
        user = self.usernamefield.text()
        password = self.passwordfield.text()

        if len(user) == 0 or len(password) == 0:
            self.errorlabel.setText("Please input all fields")
        else:
            self.errorlabel.setText("")
        
        try:
            r = dbInterface.login(user, password)
        except Exception as e:
            self.errorlabel.setText("Bad Connection")
            send_msg("Error Message", str(e), QMessageBox.Warning, e)
            logging.getLogger(self.mod_name).error(str(e))
            return
        if r.status_code != 200:
            self.errorlabel.setText("Wrong username/password")
            return
        self.jwt_token = r.content
        self.gotoSearch(self.jwt_token)

    def gotoSearch(self, token):
        print("go to search")
        raise Exception
        #search = SearchScreen(token)
        #self.window().addWidget(search)
        #self.window().setCurrentIndex(self.window().currentIndex() + 1)


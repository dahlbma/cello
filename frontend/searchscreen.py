import sys, dbInterface, os, logging
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow
from cellolib import *

class SearchScreen(QMainWindow):
    def __init__(self, token, regno=None):
        super(SearchScreen, self).__init__()
        self.token = token
        self.mod_name = "search"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/searchwindow.ui"), self)
        self.window().setWindowTitle("Search")
        self.dirty = False
        self.populated = False

from re import S
import sys, os, logging
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow

from cellolib import *

class BoxesScreen(QMainWindow):
    def __init__(self, token):
        super(BoxesScreen, self).__init__()
        self.token = token
        self.mod_name = "boxes"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/boxeswindow.ui"), self)
        self.window().setWindowTitle("Boxes")
        self.goto_search_btn.clicked.connect(self.gotoSearch)

    def gotoSearch(self):
        from searchscreen import SearchScreen
        resize_window(self)
        search = SearchScreen(self.token)
        self.window().addWidget(search)
        self.window().setCurrentIndex(self.window().currentIndex() + 1)
        search.vial_search_eb.setFocus()
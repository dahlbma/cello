import sys, os, logging, re
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from cellolib import *

class PlatesScreen(QMainWindow):
    from cellolib import gotoSearch, gotoVials, gotoBoxes, gotoMicrotubes
    def __init__(self, token):
        super(PlatesScreen, self).__init__()
        self.token = token
        self.mod_name = "plates"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/plateswindow.ui"), self)
        self.window().setWindowTitle("Plates")

        self.goto_search_btn.clicked.connect(self.gotoSearch)
        self.goto_vials_btn.clicked.connect(self.gotoVials)
        self.goto_boxes_btn.clicked.connect(self.gotoBoxes)
        self.goto_microtubes_btn.clicked.connect(self.gotoMicrotubes)

        self.new_plates_save_btn.clicked.connect(self.createPlates)
        self.new_plates_save_btn.setEnabled(False)
        types = [None, "96", "384", "1536"]
        self.new_plates_type_cb.addItems(types)
        self.new_plates_type_cb.currentTextChanged.connect(self.check_plates_input)

        self.plate_discard_chk.stateChanged.connect(self.readyDiscard)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            if self.plates_tab_wg.currentIndex() == 0:
                # press button
                return
            else: # index = 1
                # maybe not?
                return

    def tabChanged(self):
        page_index = self.plates_tab_wg.currentIndex()
        if page_index == 0:
            return
        elif page_index == 1:
            return
        elif page_index == 2:
            return

    def check_plates_input(self):
        if (self.new_plates_type_cb.currentText() != "") and \
            (self.new_plate_comment_eb.text() != ""):
            self.new_plates_save_btn.setEnabled(True)
        else:
            self.new_plates_save_btn.setEnabled(False)

    def createPlates(self):
        type = self.new_plates_type_cb.currentText()
        name = self.new_plate_comment_eb.text()
        nr_o_ps = self.new_n_plates_sb.value()
        try:
            res, status = dbInterface.createPlates(self.token, type, name, nr_o_ps)
            if not status:
                raise Exception
            self.new_plates_res_lab.setText(res)
        except:
            logging.getLogger(self.mod_name).info(f"create plates [{type}:{name}:{nr_o_ps}] failed:\n{res}")

    def check_plate_search_input(self):
        pattern = '^test$'
        t = self.plate_search_eb.text()
        if re.match(pattern, t):
            self.plateSearch()
        else:
            self.plate_search = None
            self.plate_table.setRowCount(0)
            self.plate_comment_btn.setEnabled(False)
            self.setDiscard(False)

    def plateSearch(self):
        plates = re.sub("[^0-9a-zA-Z]+", " ", self.plate_search_eb.text())

    def setDiscard(self, state):
        if state:
            self.plate_discard_chk.setEnabled(True)
        else: 
            self.plate_discard_chk.setChecked(False)
            self.plate_discard_chḱ.setEnabled(False)
    
    def readyDiscard(self):
        if self.plate_discard_chk.isChecked():
            self.plate_discard_btn.setEnabled(True)
        else:
            self.plate_discard_btn.setEnabled(False)
import re, sys, os, logging
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow

from cellolib import *

class SearchScreen(QMainWindow):
    def __init__(self, token):
        super(SearchScreen, self).__init__()
        self.token = token
        self.mod_name = "search"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/searchwindow.ui"), self)
        self.window().setWindowTitle("Search")

        self.goto_boxes_btn.clicked.connect(self.gotoBoxes)

        self.mult_vial_search_btn.clicked.connect(self.search_many_vials)
        self.vial_search_eb.textChanged.connect(self.check_vial_search_input)
        self.onevial_checkout_cb.addItems([None,
                                           'a location',
                                           'another location',
                                           'a third location'])
        self.discard_vial_btn.clicked.connect(self.discardVial)
        self.print_label_btn.clicked.connect(self.printLabel)

    def gotoBoxes(self):
        from boxesscreen import BoxesScreen
        resize_window(self)
        boxes = BoxesScreen(self.token)
        self.window().addWidget(boxes)
        self.window().setCurrentIndex(self.window().currentIndex() + 1)

    def search_many_vials(self):
        vials = self.mult_vial_search_eb.text()
        print(vials)
        res = dbInterface.getManyVials(self.token, vials)
        print(res)
        
    def check_vial_search_input(self):
        print("verify input")
        pattern = '^v[0-9]{6}$'
        t = self.vial_search_eb.text()
        if re.match(pattern, t):
            print(f"pattern match: {t}")
            self.searchVial(t)

    def searchVial(self, vialId):
        res = dbInterface.getVialInfo(self.token, vialId)
        try:
            ret = json.loads(res)
        except:
            self.errorlabel.setText(res)
            self.onevial_batch_eb.setText('')
            self.onevial_compound_id_eb.setText('')
            self.onevial_box_loc_eb.setText('')
            self.onevial_coords_eb.setText('')
            self.onevial_checkout_cb.setCurrentText(None)
            self.structure_lab.clear()
            print(res)
            return
        self.errorlabel.setText('')
        print(f'ret: {ret}')
        self.onevial_batch_eb.setText(ret[0]['batch_id'])
        self.onevial_compound_id_eb.setText(ret[0]['compound_id'])
        self.onevial_box_loc_eb.setText(ret[0]['box_id'])
        self.onevial_coords_eb.setText(str(ret[0]['coordinate']))
        self.onevial_checkout_cb.setCurrentText('a location')
        displayMolfile(self, vialId)

    def discardVial(self):
        print(f"discard vial {self.vial_search_eb.text()}")

    def printLabel(self):
        print(f"print label {self.vial_search_eb.text()}")

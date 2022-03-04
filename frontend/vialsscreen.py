import sys, os, logging, re
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from cellolib import *

class VialsScreen(QMainWindow):
    from cellolib import gotoSearch, gotoVials, gotoBoxes, gotoMicrotubes#, gotoLocations
    def __init__(self, token):
        super(VialsScreen, self).__init__()
        self.token = token
        self.mod_name = "vials"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/vialswindow.ui"), self)
        self.window().setWindowTitle("Vials")

        self.goto_search_btn.clicked.connect(self.gotoSearch)
        self.goto_boxes_btn.clicked.connect(self.gotoBoxes)
        self.goto_microtubes_btn.clicked.connect(self.gotoMicrotubes)
        self.edit_vial_error_lab.setText('')

        self.vials_tab_wg.setCurrentIndex(0)
        self.vials_tab_wg.currentChanged.connect(self.tabChanged)

        self.edit_vial_id_eb.textChanged.connect(self.check_vial_search_input)

        types = [None, "10", "20", "50", "Solid"]
        self.edit_vconc_cb.addItems(types)


    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            if self.vials_tab_wg.currentIndex() == 0:
                # press button
                self.check_vial_search_input()
                return
            else: # index = 1
                # maybe not?
                return

    def tabChanged(self):
        page_index = self.vials_tab_wg.currentIndex()
        if page_index == 0:
            self.edit_vial_id_eb.setFocus()
        elif page_index == 1:
            self.browse_btn.setFocus()
            self.structure_lab.clear()
        elif page_index == 2:
            self.create_n_vial_eb.setFocus()
            self.structure_lab.clear()

    def check_vial_search_input(self):
        pattern = '^[vV][0-9]{6}$'
        t = self.edit_vial_id_eb.text()
        if re.match(pattern, t):
            self.searchVial(t)

    def searchVial(self, vialId):
        self.edit_vial_error_lab.setText('')
        vialId = re.sub("[^0-9a-zA-Z]+", " ", vialId)
        logging.getLogger(self.mod_name).info(f"vial search {vialId}")
        #res = [{'':5}]#dbInterface.<>(self.token, vialId)
        res = dbInterface.verifyVial(self.token, vialId)
        try:
            self.vial_data = json.loads(str(res))
        except:
            self.vial_data = None
            self.v_search = False
            self.edit_update_btn.setEnabled(False)
            self.errorlabel.setText(str(res))
            self.edit_batch_id_eb.setText('')
            self.edit_compound_id_eb.setText('')
            self.edit_form_weight_eb.setText('')
            self.edit_tare_eb.setText('')
            self.edit_vconc_cb.setCurrentText(None)
            self.edit_gross_weight_eb.setText('')
            self.edit_net_weight_eb.setText('')
            self.edit_dilution_eb.setText('')
            self.structure_lab.clear()
            return
        logging.getLogger(self.mod_name).info(f"receieved {self.vial_data}")
        self.v_search = True
        self.edit_update_btn.setEnabled(True)
        self.edit_update_btn.clicked.connect(self.updateVial)
        self.errorlabel.setText('')
        self.edit_batch_id_eb.setText(f"{self.vial_data[0]['batch_id']}")
        self.edit_compound_id_eb.setText(f"{self.vial_data[0]['compound_id']}")
        self.edit_form_weight_eb.setText(f"{self.vial_data[0]['batch_formula_weight']}")
        self.edit_tare_eb.setText(f"{self.vial_data[0]['tare']}")
        self.edit_vconc_cb.setCurrentText(f"{self.vial_data[0]['conc']}")
        self.edit_gross_weight_eb.setText(f"{self.vial_data[0]['gross']}")
        self.edit_net_weight_eb.setText(f"{self.vial_data[0]['net']}")
        self.edit_dilution_eb.setText(f"{self.vial_data[0]['dilution_factor']}")
        displayMolfile(self, vialId)

    def updateVial(self):
        res, l = dbInterface.editVial(self.token,
                                      self.edit_vial_id_eb.text(),
                                      self.edit_batch_id_eb.text(),
                                      self.edit_tare_eb.text(),
                                      self.edit_gross_weight_eb.text(),
                                      self.edit_net_weight_eb.text(),
                                      self.edit_vconc_cb.currentText())
        try:
            if l == False:
                self.edit_vial_error_lab.setText(res)
            self.edit_dilution_eb.setText(str(res[0]['dilution_factor']))
            self.edit_vial_error_lab.setText('')
        except Exception as e:
            print(str(e))

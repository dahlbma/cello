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

        self.vials_tab_wg.setCurrentIndex(0)
        self.vials_tab_wg.currentChanged.connect(self.tabChanged)

        self.edit_vial_id_eb.textChanged.connect(self.check_vial_search_input)

        types = [None, "10mM", "50mM", "Solid", "2mM", "20mM"]
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
        vialId = re.sub("[^0-9a-zA-Z]+", " ", vialId)
        logging.getLogger(self.mod_name).info(f"vial search {vialId}")
        res = [{'':5}]#dbInterface.<>(self.token, vialId)
        try:
            self.vial_data = json.loads(res)
        except:
            self.vial_data = None
            self.v_search = False
            self.edit_update_btn.setEnabled(False)
            self.errorlabel.setText(res)
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
        self.errorlabel.setText('')
        self.edit_batch_id_eb.setText(f"{self.vial_data[0]['']}")
        self.edit_compound_id_eb.setText(f"{self.vial_data[0]['']}")
        self.edit_form_weight_eb.setText(f"{self.vial_data[0]['']}")
        self.edit_tare_eb.setText(f"{self.vial_data[0]['']}")
        self.edit_vconc_cb.setCurrentText(None)
        self.edit_gross_weight_eb.setText(f"{self.vial_data[0]['']}")
        self.edit_net_weight_eb.setText(f"{self.vial_data[0]['']}")
        self.edit_dilution_eb.setText(f"{self.vial_data[0]['']}")
        displayMolfile(self, vialId)
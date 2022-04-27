import sys, os, logging, re
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from cellolib import *

class VialsScreen(QMainWindow):
    from cellolib import gotoSearch, gotoBoxes, gotoMicrotubes, gotoPlates
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
        self.goto_plates_btn.clicked.connect(self.gotoPlates)

        self.edit_vial_error_lab.setText('')

        self.vials_tab_wg.setCurrentIndex(0)
        self.vials_tab_wg.currentChanged.connect(self.tabChanged)

        self.edit_vial_id_eb.textChanged.connect(self.check_vial_search_input)
        self.edit_update_btn.clicked.connect(self.updateVial)

        types = [' ', "10", "20", "50", "Solid"]
        self.edit_vconc_cb.addItems(types)

        self.browse_btn.clicked.connect(self.import_tare_file)
        self.create_vials_btn.clicked.connect(self.create_empty_vials)
        self.upload_btn.clicked.connect(self.addTare)
        self.upload_btn.setEnabled(False)
        self.upload_copy_log_btn.clicked.connect(self.copyLog)
        self.upload_copy_log_btn.setEnabled(False)


    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            if self.vials_tab_wg.currentIndex() == 0:
                return
            else:
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
            self.edit_vconc_cb.setCurrentText(' ')
            self.edit_gross_weight_eb.setText('')
            self.edit_net_weight_eb.setText('')
            self.edit_dilution_eb.setText('')
            self.structure_lab.clear()
            logging.getLogger(self.mod_name).info(f"vial search for {vialId} returned: {res}")
            return
        logging.getLogger(self.mod_name).info(f"receieved {self.vial_data}")
        self.v_search = True
        self.edit_update_btn.setEnabled(True)
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
            dbInterface.printVialLabel(self.token, self.edit_vial_id_eb.text())
            self.check_vial_search_input()
        except Exception as e:
            logging.getLogger(self.mod_name).error(str(e))


    
    def import_tare_file(self):
        self.tare_fname = QFileDialog.getOpenFileName(self, 'Import Tare File', 
                                                '.', "")
        if self.tare_fname[0] == '':
            self.upload_btn.setEnabled(False)
            return

        self.file_status_lab.setText(self.tare_fname[0])
        self.file_status_lab.setToolTip(self.tare_fname[0])
        self.upload_btn.setEnabled(True)
        self.upload_btn.setFocus()


    def addTare(self):
        try:
            with open(self.tare_fname[0], "r") as f:
                r, b = dbInterface.uploadTaredVials(self.token, f)
                res = json.loads(r)
                self.upload_result_lab.setText(f'''File: {self.tare_fname[0]}
    Failed vials: {res['FailedVials']}
    Nr of ok vials: {res['iOk']}
    Nr of failed vials: {res['iError']}\n\n''')
                if b is False:
                    raise Exception
                self.tare_fname = None
                self.file_status_lab.setText("")
                self.file_status_lab.setToolTip(None)
        except:
            print(f"addTare failed with response: {r}")

        self.upload_btn.setEnabled(False)
        self.upload_copy_log_btn.setEnabled(True)
    
    def copyLog(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.upload_result_lab.text())


    def create_empty_vials(self):
        iNrVials = self.create_n_vial_eb.text()
        res = dbInterface.createEmptyVials(self.token, iNrVials)
        out = "Vials created:\n" + "\n".join(list(json.loads(res)))
        self.empty_vials_result_lab.setText(out)
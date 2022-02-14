import re, sys, os, logging
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem

from cellolib import *

class SearchScreen(QMainWindow):
    from cellolib import gotoSearch, gotoVials, gotoBoxes#, gotoLocations, gotoMicrotubes
    def __init__(self, token):
        super(SearchScreen, self).__init__()
        self.token = token
        self.mod_name = "search"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/searchwindow.ui"), self)
        self.window().setWindowTitle("Search")

        self.goto_vials_btn.clicked.connect(self.gotoVials)
        self.goto_boxes_btn.clicked.connect(self.gotoBoxes)        

        self.search_tab_wg.setCurrentIndex(0)
        self.search_tab_wg.currentChanged.connect(self.tabChanged)

        self.multvial_export_btn.clicked.connect(self.export_multvial_table)
        self.multvial_export_btn.setEnabled(False)
        self.multvial_table.currentItemChanged.connect(self.multvial_moldisplay)

        self.mult_vial_search_btn.clicked.connect(self.search_many_vials)

        self.batch_search_btn.clicked.connect(self.search_batches)
        self.batch_export_btn.clicked.connect(self.export_batch_table)
        self.batch_export_btn.setEnabled(False)
        self.batch_table.currentItemChanged.connect(self.batch_moldisplay)

        self.v_search = False
        self.vial_search_eb.textChanged.connect(self.check_vial_search_input)
        self.onevial_checkout_cb.addItems([None,
                                           'a location',
                                           'another location',
                                           'a third location'])
        self.discard_vial_btn.clicked.connect(self.discardVial)
        self.print_label_btn.clicked.connect(self.printLabel)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            if self.search_tab_wg.currentIndex() == 1:
                self.search_many_vials()
                return
            elif self.search_tab_wg.currentIndex() == 2:
                self.search_batches()
                return
            else: # tab 0, no btn
                return

    def tabChanged(self):
        page_index = self.search_tab_wg.currentIndex()
        self.structure_lab.clear()
        if page_index == 0:
            self.vial_search_eb.setFocus()
            if self.v_search is True:
                displayMolfile(self, self.vial_search_eb.text())
        elif page_index == 1:
            self.mult_vial_search_eb.setFocus()
            self.multvial_moldisplay()
        elif page_index == 2:
            self.batch_search_eb.setFocus()
            self.batch_moldisplay()

    #def gotoVials(self):
    #    from vialsscreen import VialsScreen
    #    resize_window(self)
    #    vials = VialsScreen(self.token)
    #    self.window().addWidget(vials)
    #    self.window().setCurrentIndex(self.window().currentIndex() + 1)
    #    vials.edit_vial_id_eb.setFocus()

    #def gotoBoxes(self):
    #    from boxesscreen import BoxesScreen
    #    resize_window(self)
    #    boxes = BoxesScreen(self.token)
    #    self.window().addWidget(boxes)
    #    self.window().setCurrentIndex(self.window().currentIndex() + 1)


    def check_vial_search_input(self):
        pattern = '^[vV][0-9]{6}$'
        t = self.vial_search_eb.text()
        if re.match(pattern, t):
            self.searchVial(t)

    def searchVial(self, vialId):
        vialId = re.sub("[^0-9a-zA-Z]+", " ", vialId)
        logging.getLogger(self.mod_name).info(f"vial search {vialId}")
        res = dbInterface.getVialInfo(self.token, vialId)
        try:
            self.vial_data = json.loads(res)
        except:
            self.vial_data = None
            self.v_search = False
            self.errorlabel.setText(res)
            self.onevial_batch_eb.setText('')
            self.onevial_compound_id_eb.setText('')
            self.onevial_box_loc_eb.setText('')
            self.onevial_coords_eb.setText('')
            self.onevial_checkout_cb.setCurrentText(None)
            self.structure_lab.clear()
            self.discard_vial_btn.setEnabled(False)
            self.print_label_btn.setEnabled(False)
            return
        logging.getLogger(self.mod_name).info(f"receieved {self.vial_data}")
        self.v_search = True
        self.errorlabel.setText('')
        self.onevial_batch_eb.setText(f"{self.vial_data[0]['batch_id']}")
        self.onevial_compound_id_eb.setText(f"{self.vial_data[0]['compound_id']}")
        self.onevial_box_loc_eb.setText(f"{self.vial_data[0]['box_id']}")
        self.onevial_coords_eb.setText(f"{self.vial_data[0]['coordinate']}")
        self.onevial_checkout_cb.setCurrentText('a location')
        self.discard_vial_btn.setEnabled(True)
        self.print_label_btn.setEnabled(True)
        displayMolfile(self, vialId)

    def discardVial(self):
        print(f"discard vial {self.vial_search_eb.text()}")

    def printLabel(self):
        print(f"print label {self.vial_search_eb.text()}")

        
    def search_many_vials(self):
        vials = self.mult_vial_search_eb.text()
        vials = re.sub("[^0-9a-zA-Z]+", " ", vials)
        logging.getLogger(self.mod_name).info(f"multvial search {vials}")
        res = dbInterface.getManyVials(self.token, vials)
        self.multvial_data = None
        try:
            self.multvial_data = json.loads(res)
        except:
            self.multvial_data = None
            self.multvial_export_btn.setEnabled(False)
            self.multvial_table.setRowCount(0)
            self.structure_lab.clear()
            return
        logging.getLogger(self.mod_name).info(f"receieved {self.multvial_data}")
        self.setMultvialTableData(self.multvial_data)
        self.multvial_table.setCurrentCell(0,0)
        self.multvial_export_btn.setEnabled(True)

    def setMultvialTableData(self, data):
        self.multvial_table.setRowCount(0)
        self.multvial_table.setRowCount(len(self.multvial_data))
        self.multvial_table.setSortingEnabled(False)
        for n in range(len(data)):
            try:
                if f"{data[n]['boxId']}" == "Not found":
                    newItem = QTableWidgetItem(f"{data[n]['vialId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.batch_table.setItem(n, 0, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['boxId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.batch_table.setItem(n, 1, newItem)
                    for i in range(2, 8):
                        newItem = QTableWidgetItem("")
                        newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                        self.batch_table.setItem(n, i, newItem)
                else:
                    newItem = QTableWidgetItem(f"{data[n]['vialId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.multvial_table.setItem(n, 0, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['boxDescription']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    newItem.setToolTip(f"{data[n]['boxId']}")
                    self.multvial_table.setItem(n, 1, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['pos']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.multvial_table.setItem(n, 2, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['path']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    newItem.setToolTip(f"{data[n]['path']}")
                    self.multvial_table.setItem(n, 3, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['batchId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.multvial_table.setItem(n, 4, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['compoundId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.multvial_table.setItem(n, 5, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['batchMolWeight']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.multvial_table.setItem(n, 6, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['dilution']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.multvial_table.setItem(n, 7, newItem)
            except:
                logging.error(f"search for {data[n]['vialId']} returned bad response: {data[n]}")
        self.multvial_table.setSortingEnabled(True)
        return

    def multvial_moldisplay(self):
        try:
            if self.multvial_table.rowCount() > 0:
                row = self.multvial_table.row(self.multvial_table.currentItem())
                vialId = self.multvial_table.item(row, 0).text()
                displayMolfile(self, vialId)
        except:
            return

    def export_multvial_table(self):
        export_table(self.multvial_table)


    def search_batches(self):
        batches = self.batch_search_eb.text()
        batches = re.sub("[^0-9a-zA-Z]+", " ", batches)
        logging.getLogger(self.mod_name).info(f"batches search {batches}")
        res = dbInterface.getBatches(self.token, batches)
        self.batches_data = None
        try:
            self.batches_data = json.loads(res)
        except:
            self.batches_data = None
            self.batch_export_btn.setEnabled(False)
            self.batch_table.setRowCount(0)
            self.structure_lab.clear()
        logging.getLogger(self.mod_name).info(f"receieved {self.batches_data}")
        self.setBatchTableData(self.batches_data)
        self.batch_table.setCurrentCell(0,0)
        self.batch_export_btn.setEnabled(True)

    def setBatchTableData(self, data):
        self.batch_table.setRowCount(0)
        self.batch_table.setRowCount(len(data))
        self.batch_table.setSortingEnabled(False)
        for n in range(len(data)): # row n
            try:
                if f"{data[n]['boxId']}" == "Not found":
                    newItem = QTableWidgetItem(f"{data[n]['vialId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.batch_table.setItem(n, 0, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['boxId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.batch_table.setItem(n, 1, newItem)
                    for i in range(2, 7):
                        newItem = QTableWidgetItem("")
                        self.batch_table.setItem(n, i, newItem)
                        newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                else:
                    newItem = QTableWidgetItem(f"{data[n]['vialId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.batch_table.setItem(n, 0, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['boxDescription']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.batch_table.setItem(n, 1, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['pos']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.batch_table.setItem(n, 2, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['path']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    newItem.setToolTip(f"{data[n]['path']}")
                    self.batch_table.setItem(n, 3, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['batchId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.batch_table.setItem(n, 4, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['compoundId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.batch_table.setItem(n, 5, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['batchMolWeight']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.batch_table.setItem(n, 6, newItem)
            except:
                logging.error(f"search for {data[n]['vialId']} returned bad response: {data[n]}")
        self.batch_table.setSortingEnabled(True)
        return

    def batch_moldisplay(self):
        try:
            if self.batch_table.rowCount() > 0:
                row = self.batch_table.row(self.batch_table.currentItem())
                vialId = self.batch_table.item(row, 0).text()
                displayMolfile(self, vialId)
        except:
            return

    def export_batch_table(self):
        export_table(self.batch_table)

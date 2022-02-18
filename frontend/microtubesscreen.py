import sys, os, logging, re
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem, QAbstractItemView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from cellolib import *

class MicrotubesScreen(QMainWindow):
    from cellolib import gotoSearch, gotoVials, gotoBoxes, gotoMicrotubes#, gotoLocations
    def __init__(self, token):
        super(MicrotubesScreen, self).__init__()
        self.token = token
        self.mod_name = "microtubes"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/microtubeswindow.ui"), self)
        self.window().setWindowTitle("Microtubes")

        self.goto_search_btn.clicked.connect(self.gotoSearch)
        self.goto_vials_btn.clicked.connect(self.gotoVials)
        self.goto_boxes_btn.clicked.connect(self.gotoBoxes)
        
        self.microtubes_tab_wg.setCurrentIndex(0)
        self.microtubes_tab_wg.currentChanged.connect(self.tabChanged)

        self.tubes_search_btn.clicked.connect(self.search_microtubes)
        self.tubes_export_btn.clicked.connect(self.export_tubes_batches_data)
        

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            if self.microtubes_tab_wg.currentIndex() == 0:
                # press button
                return
            else: # index = 1
                # maybe not?
                return

    def tabChanged(self):
        page_index = self.microtubes_tab_wg.currentIndex()
        if page_index == 0:
            self.structure_lab.clear()
        elif page_index == 1:
            self.structure_lab.clear()
        elif page_index == 2:
            self.structure_lab.clear()

    def search_microtubes(self):
        batches = self.tubes_batch_eb.text()
        batches = re.sub("[^0-9a-zA-Z]+", " ", batches)
        if len(batches < 1):
            return
        logging.getLogger(self.mod_name).info(f"microtubes batch search for [{batches}]")
        res = dbInterface.getMicroTubeByBatch(self.token, batches)
        self.batches_data = None
        try:
            self.batches_data = json.loads(res)
        except:
            self.batches_data = None
            self.tubes_export_btn.setEnabled(False)
            self.tubes_batches_table.setRowCount(0)
            self.structure_lab.clear()
            return
        logging.getLogger(self.mod_name).info(f"receieved {len(self.batches_data)} responses")
        self.setTubesBatchesTableData(self.batches_data)
        self.tubes_batches_table.setCurrentCell(0,0)
        self.tubes_export_btn.setEnabled(True)

    def setTubesBatchesTableData(self, data):
        self.tubes_batches_table.setRowCount(0)
        self.tubes_batches_table.setRowCount(len(self.batches_data))
        self.tubes_batches_table.setSortingEnabled(False)
        for n in range(len(data)):
            try:
                if f"{data[n]['batchId']}" == "Not found":
                    newItem = QTableWidgetItem(f"{data[n]['batchId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.tubes_batches_table.setItem(n, 0, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['tubeId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.tubes_batches_table.setItem(n, 1, newItem)
                    for i in range(2, 6):
                        newItem = QTableWidgetItem("")
                        newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                        self.tubes_batches_table.setItem(n, i, newItem)
                else:
                    newItem = QTableWidgetItem(f"{data[n]['batchId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.tubes_batches_table.setItem(n, 0, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['tubeId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.tubes_batches_table.setItem(n, 1, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['volume']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.tubes_batches_table.setItem(n, 2, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['matrixId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.tubes_batches_table.setItem(n, 3, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['position']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.tubes_batches_table.setItem(n, 4, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['location']}")
                    newItem.setToolTip(f"{data[n]['location']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.tubes_batches_table.setItem(n, 5, newItem)
            except:
                logging.error(f"search for {data[n]['batchId']} returned bad response: {data[n]}")
        self.tubes_batches_table.setSortingEnabled(True)
        return

    def export_tubes_batches_data(self):
        export_table(self.tubes_batches_table)
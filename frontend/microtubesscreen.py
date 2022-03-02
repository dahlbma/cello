import select
import sys, os, logging, re
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QTreeWidget, QFileDialog
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
        self.tubes_ids_export_btn.clicked.connect(self.export_tube_ids)


        self.rack_search_btn.clicked.connect(self.search_rack)
        self.rack_export_btn.clicked.connect(self.export_rack_data)

        self.rack_table.currentItemChanged.connect(self.rack_moldisplay)

        self.choose_file_btn.clicked.connect(self.getRackFile)
        self.upload_file_btn.clicked.connect(self.uploadRackFile)

        self.addRows()
        self.create_add_rows_btn.clicked.connect(self.addRows)
        self.create_microtubes_table.cellChanged.connect(self.checkEmpty)
        self.create_microtubes_btn.clicked.connect(self.sendMicrotubes)


    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            if self.microtubes_tab_wg.currentIndex() == 0:
                self.search_microtubes()
                return
            elif self.microtubes_tab_wg.currentIndex() == 1:
                self.search_rack()
                return
            

    def tabChanged(self):
        page_index = self.microtubes_tab_wg.currentIndex()
        self.structure_lab.clear()
        if page_index == 0:
            self.tubes_batch_eb.setFocus()
        elif page_index == 1:
            self.rack_search_eb.setFocus()
            self.rack_moldisplay()
        elif page_index == 2:
            self.choose_file_btn.setFocus()
            self.upload_result_lab.setText('')
        elif page_index == 3:
            self.create_add_rows_btn.setFocus()

    def search_microtubes(self):
        batches = self.tubes_batch_eb.text()
        batches = re.sub("[^0-9a-zA-Z]+", " ", batches)
        if len(batches) < 1:
            return
        logging.getLogger(self.mod_name).info(f"microtubes batch search for [{batches}]")
        res = dbInterface.getMicroTubes(self.token, batches)
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

    def export_tube_ids(self):
        selectedItems = self.tubes_batches_table.selectedItems()
        selectedRows = []
        exportIds = []
        for item in selectedItems:
            if item.row() not in selectedRows:
                selectedRows.append(item.row())
                exportIds.append(self.tubes_batches_table.item(item.row(), 1).text())
        exportString = "\n".join(exportIds)
        

        fname = QFileDialog.getSaveFileName(self, 'Save to File', '.', "")
        if fname[0] == '':
            return
        with open(fname[0], "w") as f:
            f.write(exportString)
        print(f"wrote to file: {fname[0]}")


    def search_rack(self):
        rack = self.rack_search_eb.text()
        if len(rack) < 1:
            return
        logging.getLogger(self.mod_name).info(f"microtubes rack search for [{rack}]")
        res = dbInterface.getRack(self.token, rack)
        self.rack_data = None
        try:
            self.rack_data = json.loads(res)
        except:
            self.rack_data = None
            self.rack_export_btn.setEnabled(False)
            self.rack_table.setRowCount(0)
            self.structure_lab.clear()
            return
        logging.getLogger(self.mod_name).info(f"receieved {len(self.rack_data)} responses")
        self.setRackTableData(self.rack_data)
        self.rack_table.setCurrentCell(0,0)
        self.rack_export_btn.setEnabled(True)

    def setRackTableData(self, data):
        self.rack_table.setRowCount(0)
        self.rack_table.setRowCount(len(self.rack_data))
        self.rack_table.setSortingEnabled(False)
        for n in range(len(data)):
            try:
                if f"{data[n]['batchId']}" == "Not found":
                    newItem = QTableWidgetItem(f"{data[n]['batchId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.rack_table.setItem(n, 0, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['tubeId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.rack_table.setItem(n, 1, newItem)
                    for i in range(2, 8):
                        newItem = QTableWidgetItem("")
                        newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                        self.rack_table.setItem(n, i, newItem)
                else:
                    newItem = QTableWidgetItem(f"{data[n]['batchId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.rack_table.setItem(n, 0, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['tubeId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.rack_table.setItem(n, 1, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['compoundId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.rack_table.setItem(n, 2, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['volume']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.rack_table.setItem(n, 3, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['matrixId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.rack_table.setItem(n, 4, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['position']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.rack_table.setItem(n, 5, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['location']}")
                    newItem.setToolTip(f"{data[n]['location']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.rack_table.setItem(n, 6, newItem)
            except:
                logging.error(f"search for {data[n]['batchId']} returned bad response: {data[n]}")
        self.rack_table.setSortingEnabled(True)
        return

    def rack_moldisplay(self):
        try:
            if self.rack_table.rowCount() > 0:
                row = self.rack_table.row(self.rack_table.currentItem())
                compoundId = self.rack_table.item(row, 2).text()
                displayMolfile(self, compoundId)
        except:
            return    

    def export_rack_data(self):
        export_table(self.rack_table)


    def getRackFile(self):
        self.upload_result_lab.setText('')
        self.upload_fname = QFileDialog.getOpenFileName(self, 'Open file', 
                                                '.', "")
        if self.upload_fname[0] == '':
            return
        
        filename = os.path.basename(self.upload_fname[0])
        self.path_lab.setText(filename)
        self.path_lab.setToolTip(self.upload_fname[0])

    def uploadRackFile(self):
        try:
            with open(self.upload_fname[0], "rb") as f:
                r, b = dbInterface.readScannedRack(self.token, f)
                res = json.loads(r)
                self.upload_result_lab.setText(f'''Rack updated: {res['sRack']}
Failed tubes: {res['FailedTubes']}
Nr of ok tubes: {res['iOk']}
Nr of failed tubes: {res['iError']}''')
        except:
            return
    
    
    def addRow(self):
        self.create_microtubes_table.insertRow(self.create_microtubes_table.rowCount())

    def addRows(self):
        for i in range(0, 10):
            self.create_microtubes_table.insertRow(self.create_microtubes_table.rowCount())


    def checkEmpty(self):
        noempty = True
        for row in range(self.create_microtubes_table.rowCount()):
            item = self.create_microtubes_table.item(row, 0)
            if not item or not item.text():
                noempty = False
        if noempty:
            self.addRow()
        item = self.create_microtubes_table.currentItem()
        r, c = getNextFreeRow(self.create_microtubes_table, item.row(), item.column())
        if r == -1:
            self.create_microtubes_table.setCurrentCell(0, 0)
            self.create_microtubes_table.scrollToItem(self.box_table.item(0, 0),
                                                      QAbstractItemView.PositionAtCenter)
        else:
            self.create_microtubes_table.setCurrentCell(r, c)
            self.create_microtubes_table.editItem(self.create_microtubes_table.item(r, c))
            self.create_microtubes_table.scrollToItem(self.create_microtubes_table.item(r, c),
                                                      QAbstractItemView.PositionAtCenter)

    def sendMicrotubes(self):
        errors = []
        success = 0
        fail = 0
        self.create_microtubes_table.cellChanged.disconnect()
        for i in range(self.create_microtubes_table.rowCount()):
            tubeItem = self.create_microtubes_table.item(i, 0)
            tubeId = ""
            if tubeItem is not None:
                tubeId = tubeItem.text()
            compBatchItem = self.create_microtubes_table.item(i, 1)
            compBatch = ""
            if compBatchItem is not None:
                compBatch = compBatchItem.text()
            volumeItem = self.create_microtubes_table.item(i, 2)
            volume = ""
            if volumeItem is not None:
                volume = volumeItem.text()
            concItem = self.create_microtubes_table.item(i, 3)
            conc = ""
            if concItem is not None:
                conc = concItem.text()

            if (tubeId == "") or (compBatch == "") or (volume == "") or (conc == ""):
                if (tubeId == "") and (compBatch == "") and (volume == "") and (conc == ""):
                    continue
                else:
                    errors.append([tubeId, compBatch, volume, conc, None])
                    continue
            # try sending it
            res, status = dbInterface.addMicrotube(self.token,
                                                   tubeId,
                                                   compBatch,
                                                   volume,
                                                   conc)
            if not status:
                #fail
                fail += 1
                errors.append([tubeId, compBatch, volume, conc, res])
            else:
                #success
                success += 1

        # flush table
        self.create_microtubes_table.setRowCount(0)
        
        # add error rows back
        self.create_microtubes_table.setRowCount(len(errors))
        for row in range(len(errors)):
            for i in range(0, 4):
                newItem = QTableWidgetItem(f"{errors[row][i]}")
                newItem.setBackground(QColor(250, 103, 92))
                self.create_microtubes_table.setItem(row, i, newItem)
            if errors[row][4] is None:
                self.create_microtubes_table.item(row, 0).setToolTip("Not enough arguments.")
            else:
                self.create_microtubes_table.item(row, 0).setToolTip(f"{errors[row][4]}")

        for i in range(0, 5):
            self.addRow()
        
        self.create_microtubes_table.setCurrentCell(0, 0)
        #self.create_microtubes_table.editItem(self.create_microtubes_table.item(0, 0))
        self.create_microtubes_table.cellChanged.connect(self.checkEmpty)

    

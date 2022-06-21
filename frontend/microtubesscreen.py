import sys, os, logging, re, csv
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QTreeWidget, QFileDialog
from PyQt5.QtWidgets import QTreeWidgetItem, QAbstractItemView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from cellolib import *

class MicrotubesScreen(QMainWindow):
    from cellolib import gotoSearch, gotoVials, gotoBoxes, gotoPlates
    def __init__(self, token, test):
        super(MicrotubesScreen, self).__init__()
        self.token = token
        self.mod_name = "microtubes"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/microtubeswindow.ui"), self)
        #self.window().setWindowTitle("Microtubes")

        self.centralwidget.setProperty("test", test)

        self.goto_search_btn.clicked.connect(self.gotoSearch)
        self.goto_vials_btn.clicked.connect(self.gotoVials)
        self.goto_boxes_btn.clicked.connect(self.gotoBoxes)
        self.goto_plates_btn.clicked.connect(self.gotoPlates)
        
        self.microtubes_tab_wg.setCurrentIndex(0)
        self.microtubes_tab_wg.currentChanged.connect(self.tabChanged)

        self.tubes_search_btn.clicked.connect(self.search_microtubes)
        self.tubes_export_btn.clicked.connect(self.export_tubes_batches_data)
        self.tubes_ids_export_btn.clicked.connect(self.export_tube_ids)
        self.tubes_batches_table.currentItemChanged.connect(self.showMicrotubeMol)

        self.rack_search_btn.clicked.connect(self.search_rack)
        self.rack_export_btn.clicked.connect(self.export_rack_data)

        self.rack_table.currentItemChanged.connect(self.rack_moldisplay)
        self.rack_table.currentItemChanged.connect(self.show_loc_id)
        self.rack_table.currentItemChanged.connect(self.check_print)

        self.rack_print_label_btn.clicked.connect(self.print_rack)
        self.rack_print_label_btn.setEnabled(False)

        self.choose_file_btn.clicked.connect(self.getRackFile)
        self.upload_file_btn.clicked.connect(self.uploadRackFile)
        self.update_box_eb.textChanged.connect(self.unlockRackUpload)
        self.upload_copy_log_btn.clicked.connect(self.copyLog)
        self.upload_copy_log_btn.setEnabled(False)

        self.new_racks_save_btn.clicked.connect(self.createRacks)
        self.new_racks_save_btn.setEnabled(True)

        self.addRows()
        self.create_add_rows_btn.clicked.connect(self.addRows)
        self.create_microtubes_table.cellChanged.connect(self.checkEmpty)
        self.create_microtubes_btn.clicked.connect(self.sendMicrotubes)
        self.create_import_btn.clicked.connect(self.create_import_file)
        self.create_export_btn.clicked.connect(self.export_create_data)

        self.clear_microtube_btn.clicked.connect(self.clear_input)

        self.move_rack_id_eb.returnPressed.connect(self.moveRackStep1)
        self.move_box_id_eb.returnPressed.connect(self.moveRackStep2)
        self.move_box_id_eb.setEnabled(False)


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
        self.rack_display.setHtml("")
        if page_index == 0:
            self.tubes_batch_eb.setFocus()
            self.showMicrotubeMol(self.tubes_batches_table.currentItem())
        elif page_index == 1:
            self.rack_search_eb.setFocus()
            self.search_rack()
            self.rack_moldisplay(self.rack_table.currentItem())
        elif page_index == 2:
            self.choose_file_btn.setFocus()
            self.upload_result_lab.setText('')
        elif page_index == 3:
            return
        elif page_index == 4:
            r, c = getNextFreeRow(self.create_microtubes_table, 0, 0, entireRowFree=True, fromSame=True)
            self.create_microtubes_table.setCurrentCell(r, c)
            self.create_microtubes_table.setFocus()
        elif page_index == 5:
            self.move_rack_id_eb.setFocus()

    def search_microtubes(self):
        self.tubes_batches_table.setRowCount(0);
        self.tubes_batches_table.update()
        batches = self.tubes_batch_eb.text()
        batches = re.sub("[^0-9a-zA-Z]+", " ", batches)
        if len(batches) < 1:
            return
        logging.getLogger(self.mod_name).info(f"microtubes batch search for [{batches}]")
        saBatches = list(batches.split())
        QApplication.setOverrideCursor(Qt.WaitCursor)
        for sBatch in saBatches:
            if len(sBatch) > 4:
                res = dbInterface.getMicroTubes(self.token, sBatch)
                try:
                    self.batches_data = json.loads(res)
                except Exception as e:
                    QApplication.restoreOverrideCursor()
                    logging.info(str(e))
                    self.batches_data = None
                    self.tubes_export_btn.setEnabled(False)
                    self.tubes_batches_table.setRowCount(0)
                    self.structure_lab.clear()
                    return
                self.appendTubesBatchesTableData(self.batches_data)

        self.batches_data = None
        self.tubes_batches_table.setCurrentCell(0,0)
        self.tubes_export_btn.setEnabled(True)
        QApplication.restoreOverrideCursor()

    def appendTubesBatchesTableData(self, data):
        rowPosition = self.tubes_batches_table.rowCount()
        self.tubes_batches_table.insertRow(rowPosition)
        self.tubes_batches_table.setSortingEnabled(False)
        for resLen in range(len(data)):
            n = rowPosition + resLen
            try:
                if f"{data[resLen]['batchId']}" == "Not found":
                    newItem = QTableWidgetItem(f"{data[resLen]['batchId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.tubes_batches_table.setItem(n, 0, newItem)
                    newItem = QTableWidgetItem(f"{data[resLen]['tubeId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.tubes_batches_table.setItem(n, 1, newItem)
                    for i in range(2, 6):
                        newItem = QTableWidgetItem("")
                        newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                        self.tubes_batches_table.setItem(n, i, newItem)
                else:
                    newItem = QTableWidgetItem(f"{data[resLen]['batchId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.tubes_batches_table.setItem(n, 0, newItem)
                    newItem = QTableWidgetItem(f"{data[resLen]['compoundId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.tubes_batches_table.setItem(n, 1, newItem)
                    newItem = QTableWidgetItem(f"{data[resLen]['tubeId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.tubes_batches_table.setItem(n, 2, newItem)
                    newItem = QTableWidgetItem(f"{data[resLen]['volume']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.tubes_batches_table.setItem(n, 3, newItem)
                    newItem = QTableWidgetItem(f"{data[resLen]['matrixId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.tubes_batches_table.setItem(n, 4, newItem)
                    newItem = QTableWidgetItem(f"{data[resLen]['position']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.tubes_batches_table.setItem(n, 5, newItem)
                    newItem = QTableWidgetItem(f"{data[resLen]['location']}")
                    newItem.setToolTip(f"{data[resLen]['location']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.tubes_batches_table.setItem(n, 6, newItem)
            except Exception as e:
                logging.error(str(e))
        self.tubes_batches_table.setSortingEnabled(True)
        return
        

    def showMicrotubeMol(self, item):
        if item is not None:
            batchId = self.tubes_batches_table.item(item.row(), 0).text()
            displayMolfile(self, batchId)
        else:
            self.structure_lab.clear()

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
        logging.getLogger(self.mod_name).info(f"wrote to file: {fname[0]}")


    def search_rack(self):
        self.rack_display.setHtml("")
        self.rack_not_found_lab.setText('')
        rack = self.rack_search_eb.text()
        if len(rack) < 6:
            self.check_print(None)
            return
        logging.getLogger(self.mod_name).info(f"microtubes rack search for [{rack}]")
        res, b = dbInterface.getRack(self.token, rack)
        if b == False:
            self.rack_not_found_lab.setText(res)
        self.rack_data = None
        try:
            self.rack_data = json.loads(res)
        except:
            self.rack_data = None   
            self.rack_export_btn.setEnabled(False)
            self.rack_table.setRowCount(0)
            self.structure_lab.clear()
            logging.getLogger(self.mod_name).info(f"microtubes rack search for [{rack}] returned: {res}")
            return
        logging.getLogger(self.mod_name).info(f"receieved {len(self.rack_data)} responses")
        self.setRackTableData(self.rack_data)
        self.rack_table.setCurrentCell(0,0)
        self.rack_export_btn.setEnabled(True)
        if len(self.rack_data) == 0:
            self.check_print("empty")
            self.rack_display.setHtml("")
        else:
            self.show_racks(self.rack_data)

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
                    newItem.setToolTip(f"{data[n]['locId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.rack_table.setItem(n, 6, newItem)
            except:
                logging.error(f"search for {data[n]['batchId']} returned bad response: {data[n]}")
        self.rack_table.setSortingEnabled(True)
        return

    def show_loc_id(self, item):
        if (self.rack_table.rowCount() > 0) and (item is not None):
            loc_id = self.rack_table.item(item.row(), 6).toolTip()
            self.rack_boxid_lab.setText(loc_id)
        else:
            self.rack_boxid_lab.setText("")
    
    def check_print(self, item):
        if item == "empty":
            l = self.rack_search_eb.text().split(" ")
            self.currentRack = l[0]
            self.rack_print_label_btn.setEnabled(True)
        elif (self.rack_table.rowCount() > 0) and (item is not None):
            self.currentRack = self.rack_table.item(item.row(), 4).text()
            self.rack_print_label_btn.setEnabled(True)
        else:
            self.currentRack = None
            self.rack_print_label_btn.setEnabled(False)


    def rack_moldisplay(self, item):
            if (self.rack_table.rowCount() > 0) and (item is not None):
                compoundId = self.rack_table.item(item.row(), 2).text()
                displayMolfile(self, compoundId)
            else:
                self.structure_lab.clear()
    
    def show_racks(self, data):
        #make copy
        data_copy = list(data)

        #separate data
        data_parts = []
        part = []
        current_rack = None
        for w in data:
            if w['matrixId'] != current_rack:
                if len(part) > 0:
                    data_parts.append(part)
                    part = []
                current_rack = w['matrixId']
            p = {'tubeId':w.pop('tubeId'), 'well':w.pop('position'), 'matrixId':w.pop('matrixId')}
            part.append(p)
        if len(part) > 0:
            data_parts.append(part)
        
        #Get html
        id_hdr = lambda x: f"<span class=\"normal\">{x}</span>"

        html = id_hdr(data_parts[0][0]['matrixId']) \
               + "</br>" \
               + chart_html(data_parts[0], 96)
        for p in data_parts[1:]:
            html += id_hdr(p[0]['matrixId']) \
                    + "</br>" \
                    + chart_html(p, 96)
        
        #Show html
        self.rack_display.setHtml(chart_lambda()(html, ""))

    def print_rack(self):
        rack = self.currentRack
        dbInterface.printRack(self.token, rack)

    def export_rack_data(self):
        export_table(self.rack_table)


    def getRackFile(self):
        self.upload_result_lab.setText('')
        self.upload_fnames = QFileDialog.getOpenFileNames(self, 'Open file', 
                                                '.', "")
        if len(self.upload_fnames[0]) == 0:
            return
        
        filename = self.upload_fnames[0][0]
        if len(self.upload_fnames[0]) > 1:
            filename += " ..."
        self.path_lab.setText(filename)
        self.path_lab.setToolTip('\n'.join(self.upload_fnames[0]))
        self.upload_result_lab.setText("Set box destination for racks.")
        self.update_box_eb.setEnabled(True)
        self.update_box_eb.clear()
        self.update_box_eb.setFocus()

    def unlockRackUpload(self, newText):
        pattern = '^[a-zA-Z]{2}[0-9]{5}$'
        if re.match(pattern, newText):
            r, b = dbInterface.verifyLocation(self.token, newText)
            if b:
                self.upload_file_btn.setEnabled(True)
            else:
                self.upload_file_btn.setEnabled(False)
        else:
            self.upload_file_btn.setEnabled(False)

    def uploadRackFile(self):
        res_txt = ""
        for file_name in self.upload_fnames[0]:
            try:
                with open(file_name, "rb") as f:
                    r, b = dbInterface.readScannedRack(self.token, self.update_box_eb.text(), f)
                    res = json.loads(r)
                    res_txt += f'''File: {file_name}
    Rack updated: {res['sRack']}
    Failed tubes: {res['FailedTubes']}
    Nr of ok tubes: {res['iOk']}
    Nr of failed tubes: {res['iError']}\n\n'''
                    f.close()
                    try:
                        os.mkdir('uploads')
                    except:
                        pass
                    try:
                        os.rename(file_name, f'uploads/{os.path.basename(file_name)}')
                    except Exception as e:
                        logging.getLogger(self.mod_name).error(f"Move rack failed: {str(e)}")
            except:
                logging.getLogger(self.mod_name).error(f"readScannedRack failed with response: {r}")

        self.update_box_eb.setEnabled(False)
        self.upload_copy_log_btn.setEnabled(True)
        self.upload_result_lab.setText(res_txt)
    
    def copyLog(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.upload_result_lab.text())


    def createRacks(self):
        nr_o_rs = self.new_n_racks_sb.value()
        try:
            res, status = dbInterface.createRacks(self.token, nr_o_rs)
            if not status:
                raise Exception
            self.new_racks_res_lab.setText(res)
            self.new_n_racks_sb.setValue(1)
        except:
            logging.getLogger(self.mod_name).info(f"create racks [{nr_o_rs}] failed:\n{res}")


    
    def addRow(self):
        self.create_microtubes_table.insertRow(self.create_microtubes_table.rowCount())

    def addRows(self):
        for i in range(0, 10):
            self.create_microtubes_table.insertRow(self.create_microtubes_table.rowCount())

    def clear_input(self):
        self.create_microtubes_table.setRowCount(0)
        self.addRows()

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
            #try sending it
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

        #flush table
        self.create_microtubes_table.setRowCount(0)
        
        #add error rows back
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
        self.create_microtubes_table.cellChanged.connect(self.checkEmpty)

    def create_import_file(self):
        fname = QFileDialog.getOpenFileName(self, 'Import from File', 
                                                '.', "")
        if fname[0] == '':
            return
        self.create_microtubes_table.cellChanged.disconnect()
        try:
            with open(fname[0], newline='') as f:
                dialect = csv.Sniffer().sniff(f.read())
                f.seek(0)
                imp_reader = csv.reader(f, dialect)
                for count, rowdata in enumerate(imp_reader):
                    current_row = self.create_microtubes_table.currentRow()
                    next_row, _ = getNextFreeRow(self.create_microtubes_table, current_row, 0, entireRowFree=True, fromSame=True)
                    if next_row == -1 or next_row == self.create_microtubes_table.rowCount():
                        next_row = self.create_microtubes_table.rowCount()
                        self.create_microtubes_table.insertRow(self.create_microtubes_table.rowCount())
                    for index, text in enumerate(rowdata):
                        if index < 4:
                            newItem = QTableWidgetItem(f"{text}")
                            self.create_microtubes_table.setItem(next_row, index, newItem)
                    rowLen = len(rowdata)
                    for index in range(rowLen, 4):
                        newItem = QTableWidgetItem("")
                        self.create_microtubes_table.setItem(next_row, index, newItem)
                for i in range(0, 5):
                    self.addRow()
        except:
            logging.getLogger(self.mod_name).error("microtube file import failed")  
        self.create_microtubes_table.cellChanged.connect(self.checkEmpty)

    def export_create_data(self):
        export_table(self.create_microtubes_table)

    def moveRackStep1(self):
        pattern = '^MX[0-9]{4}$'
        rack_id = self.move_rack_id_eb.text()
        if re.match(pattern, rack_id):
            self.move_status_lab.setText("Rack Id OK.\nInput box location to move to.")
            self.move_box_id_eb.setEnabled(True)
            self.move_box_id_eb.setFocus()
            return
        else:
            self.move_status_lab.setText(f"Rack Id {rack_id} not OK.\nPlease check input.")
            self.move_box_id_eb.clear()
            self.move_rack_id_eb.clear()
            self.move_box_id_eb.setEnabled(False)
            self.move_rack_id_eb.setFocus()
            return
    
    def moveRackStep2(self):
        pattern = '^[a-zA-Z]{2}[0-9]{5}$'
        rack_id = self.move_rack_id_eb.text() #should be OK
        box_id = self.move_box_id_eb.text()
        self.move_status_lab.clear()
        if re.match(pattern, box_id):
            try:
                r, status = dbInterface.updateRackLocation(self.token, rack_id, box_id)
                if status is False:
                    raise Exception
            except:
                logging.getLogger(self.mod_name).error(f"Rack move failed: {rack_id}>{box_id}: {r}")
                self.move_status_lab.setText(f"\nRack move failed: {rack_id}>{box_id}: {r}")
                return
            #all ok
            logging.getLogger(self.mod_name).info(f"Move successful: {rack_id}>{box_id}")
            self.move_status_lab.setText("Move Successful.")
            self.move_rack_id_eb.clear()
            self.move_rack_id_eb.setFocus()
            self.move_box_id_eb.clear()
            self.move_box_id_eb.setEnabled(False)

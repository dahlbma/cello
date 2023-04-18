import sys, os, logging, re, csv
from unittest import skip
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QIntValidator, QIcon
from PyQt5 import QtWebEngineWidgets

from cellolib import *

class PlatesScreen(QMainWindow):
    from cellolib import gotoSearch, gotoVials, gotoBoxes, gotoMicrotubes
    def __init__(self, token, test):
        super(PlatesScreen, self).__init__()
        self.token = token
        self.mod_name = "plates"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/plateswindow.ui"), self)

        self.centralwidget.setProperty("test", test)
      
        self.nine6to384_btn.setIcon(QIcon(resource_path("assets/arrow.png")))

        self.goto_search_btn.clicked.connect(self.gotoSearch)
        self.goto_vials_btn.clicked.connect(self.gotoVials)
        self.goto_boxes_btn.clicked.connect(self.gotoBoxes)
        self.goto_microtubes_btn.clicked.connect(self.gotoMicrotubes)

        self.plates_tab_wg.setCurrentIndex(0)
        self.new_plates_comment_eb.setFocus()
        self.plates_tab_wg.currentChanged.connect(self.tabChanged)

        self.new_plates_save_btn.clicked.connect(self.createPlates)
        self.new_plates_save_btn.setEnabled(False)

        types = [' ', "96", "384", "1536"]
        self.new_plates_type_cb.addItems(types)
        self.new_plates_type_cb.currentTextChanged.connect(self.check_plates_input)
        
        self.new_plates_comment_eb.textChanged.connect(self.check_plates_input)

        locations = ['Compound Center', "CC Freezer A", "CC Freezer B", "Sent to User"]
        self.plate_location_cb.addItems(locations)
        locations.append(' ')
        self.update_plate_location_cb.addItems(locations)
        
        self.label_to_plates_save_btn.clicked.connect(self.createPlatesFromLabel)
        self.label_to_plates_save_btn.setEnabled(False)
        self.label_to_plates_type_cb.addItems(types)
        self.label_to_plates_type_cb.currentTextChanged.connect(self.label_check_plates_input)
        self.label_to_plates_comment_eb.textChanged.connect(self.label_check_plates_input)
        self.label_to_plate_id_eb.textChanged.connect(self.label_check_plates_input)

        self.plate_data = None
        self.plate_search_dict = None
        self.plate_search_btn.clicked.connect(self.check_plate_search_input)
        self.plate_comment_btn.clicked.connect(self.updatePlate)
        self.plate_discard_btn.clicked.connect(self.discardPlate)
        self.setDiscard(False)
        self.plate_discard_chk.stateChanged.connect(self.readyDiscard)
        self.plate_export_btn.clicked.connect(self.plate_export_data)
        self.plate_print_btn.clicked.connect(self.printPlate)
        self.plate_print_btn.setEnabled(False)

        self.plate_table.currentItemChanged.connect(self.plate_moldisplay)

        self.upload_populated = False
        self.data_issue = False
        self.upload_file_btn.setEnabled(False)

        self.upload_plate_size_cb.addItems(types)
        self.upload_plate_size_cb.currentTextChanged.connect(self.enable_upload)

        self.choose_file_btn.clicked.connect(self.import_plates_file)
        self.upload_file_btn.clicked.connect(self.upload_plate_table)
        self.upload_export_btn.clicked.connect(self.export_upload_data)
        self.upload_pbar.setValue(0)
        self.upload_pbar.hide()

        self.upload_plates_table.currentItemChanged.connect(self.upload_moldisplay)

        self.nine6to384_btn.clicked.connect(self.nine6to384_merge)
        self.nine6to384_btn.setEnabled(False)

        self.plate_ids = [-1]*5 # i=0: result, i=1:q1, ...
        self.dom_size = -1
        self.mod_arr = [0]*5 
        self.size_arr = [-1]*5
        self.ok_arr = [False]*5

        self.merge_datas = [None]*5

        self.currentTexts = [""]*6 # i=0: result, i=1:q1, ..., i=5:volume_eb

        self.join_q1_eb.textChanged.connect(self.mod1)
        self.join_q2_eb.textChanged.connect(self.mod2)
        self.join_q3_eb.textChanged.connect(self.mod3)
        self.join_q4_eb.textChanged.connect(self.mod4)
        self.join_result_eb.textChanged.connect(self.mod0)
        self.merge_volume_eb.textChanged.connect(self.mod_vol)

        validator = QIntValidator(0, 1000, self)
        self.merge_volume_eb.setValidator(validator)


    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            if self.plates_tab_wg.currentIndex() == 0:
                return
            elif self.plates_tab_wg.currentIndex() == 2:
                self.check_plate_search_input()
            else:
                return

    def tabChanged(self):
        page_index = self.plates_tab_wg.currentIndex()
        self.structure_lab.clear()
        self.plate_display.setHtml("")
        if page_index == 0:
            self.new_plates_comment_eb.setFocus()
        elif page_index == 1:
            self.label_to_plate_id_eb.setFocus()
        elif page_index == 2:
            self.plate_search_eb.setFocus()
            self.plate_moldisplay(self.plate_table.currentItem())
            self.check_plate_search_input()
        elif page_index == 3:
            self.choose_file_btn.setFocus()
            self.upload_moldisplay(self.upload_plates_table.currentItem())
        elif page_index == 4:
            self.join_q1_eb.setFocus()
            self.showMergePlates()
            #self.move_focus(0, self.ok_arr)

    def check_plates_input(self):
        if (self.new_plates_type_cb.currentText() != ' ') and \
            (self.new_plates_comment_eb.text() != ""):
            self.new_plates_save_btn.setEnabled(True)
        else:
            self.new_plates_save_btn.setEnabled(False)

    def label_check_plates_input(self):
        sPlateId = self.label_to_plate_id_eb.text()
        sPlateId = sPlateId.rstrip()
        pattern = '^[pP]{1}[0-9]{6}$'
        t = re.sub("[^0-9a-zA-Z]+", " ", sPlateId)
        lValidPlate = False
        if re.match(pattern, t):
            lValidPlate = True
            
        if (lValidPlate and self.label_to_plates_type_cb.currentText() != ' ') and \
            (self.label_to_plates_comment_eb.text() != ""):
            self.label_to_plates_save_btn.setEnabled(True)
        else:
            self.label_to_plates_save_btn.setEnabled(False)

    def createPlates(self):
        type = self.new_plates_type_cb.currentText()
        location = self.plate_location_cb.currentText()
        name = self.new_plates_comment_eb.text()
        nr_o_ps = self.new_n_plates_sb.value()
        try:
            res, status = dbInterface.createPlates(self.token, type, name, nr_o_ps, location)
            if not status:
                raise Exception
            self.new_plates_res_lab.setText(res)
            self.new_plates_type_cb.setCurrentText(' ')
            self.new_plates_comment_eb.setText("")
            self.new_n_plates_sb.setValue(1)
        except:
            logging.getLogger(self.mod_name).info(f"create plates [{type}:{name}:{nr_o_ps}] failed:\n{res}")

    def createPlatesFromLabel(self):
        type = self.label_to_plates_type_cb.currentText()
        name = self.label_to_plates_comment_eb.text()
        nr_o_ps = self.label_to_n_plates_sb.value()
        sStartPlate = self.label_to_plate_id_eb.text()
        try:
            res, status = dbInterface.createPlatesFromLabel(self.token,
                                                            sStartPlate,
                                                            type,
                                                            name,
                                                            nr_o_ps)
            if not status:
                self.label_to_plates_res_lab.setText(res)
                raise Exception
            self.label_to_plates_res_lab.setText(res)
            self.label_to_plates_type_cb.setCurrentText(' ')
            self.label_to_plates_comment_eb.setText("")
            self.label_to_plate_id_eb.setText("")
            self.label_to_n_plates_sb.setValue(1)
        except:
            logging.getLogger(self.mod_name).info(f"create plates from label [{type}:{name}:{nr_o_ps}] failed:\n{res}")

    def check_plate_search_input(self):
        pattern = '^[pP]{1}[0-9]{6}$'
        sPlateId = self.plate_search_eb.text()
        sPlateId = sPlateId.rstrip()
        self.plate_search_eb.setText(sPlateId)
        t = re.sub("[^0-9a-zA-Z]+", " ", sPlateId)
        if re.match(pattern, t):
            self.plateSearch(t)
        else:
            self.plate_search = None
            self.plate_data = None
            self.plate_comment_eb.setText("")
            self.plate_comment_eb.setEnabled(False)
            self.plate_comment_btn.setEnabled(False)
            self.plate_table.setRowCount(0)
            self.plate_print_btn.setEnabled(False)
            self.setDiscard(False)

    def plateSearch(self, plate):
        if len(plate) < 1:
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        logging.getLogger(self.mod_name).info(f"plate search {plate}")
        res, status = dbInterface.getPlate(self.token, plate)
        try:
            self.plate_data = json.loads(res)
            if (len(self.plate_data) < 1) or status != 200:
                raise Exception
            self.platesearch_error_lab.setText("")
            logging.getLogger(self.mod_name).info(f"received data")
            self.plate_comment_eb.setEnabled(True)
            self.plate_comment_btn.setEnabled(True)
            self.plate_comment_eb.setText(self.plate_data[0]['description'])
            self.setPlateTableData(self.plate_data)
            self.plate_table.setCurrentCell(0,0)
            r, _ = dbInterface.verifyPlate(self.token, plate)
            info = json.loads(r)
            self.update_plate_location_cb.setCurrentText(info[0]['loc_id'])
            if info[0]['discarded'] == '1':
                self.platesearch_error_lab.setText(f"DISCARDED")
            else:
                self.platesearch_error_lab.setText(f"Plate size: {info[0]['wells']}")
            self.plate_display.setHtml(plate_to_html(self.plate_data, info[0]['wells'], None, None))
            self.setDiscard(False)
            self.setDiscard(True)
            self.plate_print_btn.setEnabled(True)
        except Exception as e:
            self.plate_comment_eb.setText("")
            self.update_plate_location_cb.setCurrentText("")
            if status == 200:
                r, _ = dbInterface.verifyPlate(self.token, plate)
                info = json.loads(r)
                self.plate_comment_eb.setText(info[0]['comments'])
                self.update_plate_location_cb.setCurrentText(info[0]['loc_id'])
                self.platesearch_error_lab.setText(f"Plate size: {info[0]['wells']}")
                self.plate_display.setHtml(plate_to_html(self.plate_data, info[0]['wells'], None, None))
                self.plate_comment_eb.setEnabled(True)
                self.plate_comment_btn.setEnabled(True)
                logging.getLogger(self.mod_name).info(f"empty plate, no data received")
            else:
                self.plate_display.setHtml("")
                self.platesearch_error_lab.setText(res)
                self.plate_comment_eb.setEnabled(False)
                self.plate_comment_btn.setEnabled(False)
                logging.getLogger(self.mod_name).info(f"search returned {res}")
            self.plate_data = None
            self.plate_table.setRowCount(0)
            self.plate_print_btn.setEnabled(False)
        QApplication.restoreOverrideCursor()
    
    def setPlateTableData(self, data):
        self.plate_table.setRowCount(0)
        self.plate_table.setRowCount(len(data))
        for n in range(len(data)):
            try:
                newItem = QTableWidgetItem(f"{data[n]['well']}")
                newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                self.plate_table.setItem(n, 0, newItem)
                newItem = QTableWidgetItem(f"{data[n]['compound_id']}")
                newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                self.plate_table.setItem(n, 1, newItem)
                newItem = QTableWidgetItem(f"{data[n]['notebook_ref']}")
                newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                self.plate_table.setItem(n, 2, newItem)
                newItem = QTableWidgetItem(f"{data[n]['form']}")
                newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                self.plate_table.setItem(n, 3, newItem)
                newItem = QTableWidgetItem(f"{data[n]['conc']}")
                newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                self.plate_table.setItem(n, 4, newItem)
                newItem = QTableWidgetItem(f"{data[n]['volume']}")
                newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                self.plate_table.setItem(n, 5, newItem)
            except:
                logging.error(f"plate search failed with data row: {data[n]}")

    def updatePlate(self):
        new_comment = self.plate_comment_eb.text()
        new_location = self.update_plate_location_cb.currentText()
        plate = self.plate_search_eb.text()
        try:
            _, status = dbInterface.updatePlateName(self.token, plate, new_comment, new_location)
            if status is False:
                raise Exception
        except:
            logging.getLogger(self.mod_name).info(f"updating comment failed")
        self.check_plate_search_input()

    def printPlate(self):
        plate = self.plate_search_eb.text()
        dbInterface.printPlateLabel(self.token, plate)

    def setDiscard(self, state):
        if state:
            self.plate_discard_chk.setEnabled(True)
        else: 
            self.plate_discard_chk.setChecked(False)
            self.plate_discard_chk.setEnabled(False)
            self.readyDiscard()
    
    def readyDiscard(self):
        if self.plate_discard_chk.isChecked():
            self.plate_discard_btn.setEnabled(True)
        else:
            self.plate_discard_btn.setEnabled(False)

    def discardPlate(self):
        plate = self.plate_search_eb.text()
        r = dbInterface.discardPlate(self.token, plate)
        logging.getLogger(self.mod_name).info(f"discardPlate [{plate}] returned: {r}")
        self.platesearch_error_lab.setText(f"DISCARDED")

    def plate_moldisplay(self, item):
        if (item is not None):
            batchId = self.plate_table.item(item.row(), 2).text()
            if len(batchId) > 0:
                displayMolfile(self, batchId)
                return
        self.structure_lab.clear()


    def plate_export_data(self):
        export_table(self.plate_table)

    def enable_upload(self):
        if (self.upload_populated is True) and \
           (self.upload_plate_size_cb.currentText() != ' ') and \
           (self.data_issue is False):
            self.upload_file_btn.setEnabled(True)
        else:
            self.upload_file_btn.setEnabled(False)

    def import_plates_file(self):
        fname = QFileDialog.getOpenFileName(self, 'Import from File', 
                                                '.', "")
        if fname[0] == '':
            return
        try:
            with open(fname[0]) as f:
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(f.read())
                f.seek(0)
                has_header = sniffer.has_header(f.read())
                f.seek(0)
                reader = csv.reader(f, dialect)
                self.path_lab.setText(fname[0])
                #self.upload_file_btn.setEnabled(True)
                self.upload_pbar.setValue(0)
                self.upload_pbar.hide()
                data = list(reader)
                if has_header:
                    data.pop(0)
                self.upload_plates_data = data
                self.populate_upload_table(data)
        except Exception as e:
            self.upload_plates_data = None
            self.upload_file_btn.setEnabled(False)
            logging.getLogger(self.mod_name).error("plates file import failed")
            logging.getLogger(self.mod_name).error(str(e))
        self.enable_upload()

    def populate_upload_table(self, data, error=False):
        if len(data) == 0:
            self.upload_populated = False
        else:
            self.data_issue = error
            self.upload_plates_table.setRowCount(0)
            self.upload_plates_table.setRowCount(len(data))
            # assume data like [{col1, col2, col3, ...}, {...}]
            try:
                iBackfillCount = 0
                iMaxRow = len(data)
                for n in range(len(data)):
                    bBackfill = False
                    if data[n][2].upper() == 'BACKFILL':
                        iBackfillCount += 1
                        bBackfill = True
                        data[n][2] = data[n][3] = 'BACKFILL'
                    for m in range(len(data[n])):
                        if (data[n][m] is None) or (len(data[n][m]) == 0):
                            self.data_issue = True
                        newItem = QTableWidgetItem(f"{data[n][m]}")
                        newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                        if error is True:
                            newItem.setBackground(QColor(250, 103, 92))
                        if bBackfill:
                            self.upload_plates_table.setItem(iMaxRow-iBackfillCount, m, newItem)
                        else:
                            self.upload_plates_table.setItem(n-iBackfillCount, m, newItem)
                    if len(data[n]) < 7:
                        self.data_issue = True
                        for k in range(len(data[n]), 7):
                            # empty cells
                            newItem = QTableWidgetItem("")
                            newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                            newItem.setBackground(QColor(250, 103, 92))
                            self.upload_plates_table.setItem(n, k, newItem)
            except Exception as e:
                logging.getLogger(self.mod_name).error("plate file import failed")
                logging.getLogger(self.mod_name).error(str(e))
            self.upload_populated = True
        

    def upload_plate_table(self):
        repopulate_data = []
        # set up progress bar
        iTickCount = 0
        iTicks = int(self.upload_plates_table.rowCount() / 100)
        progress = 0
        self.upload_pbar.setValue(progress)
        self.upload_pbar.show()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        currentPlate = None
        plateType = self.upload_plate_size_cb.currentText()
        flush = False
        for row in range(self.upload_plates_table.rowCount()):
            QApplication.processEvents()
            plate_id = self.upload_plates_table.item(row, 0).text()
            if plate_id != currentPlate:
                res, ok = dbInterface.setPlateType(self.token, plate_id, plateType)
                currentPlate = plate_id
                if ok is False:
                    logging.getLogger(self.mod_name).error(f"set plate type [{plate_id}:{plateType}] failed with response: [{res.content.decode()}:{res.status_code}]\nIgnoring plate [{plate_id}]")
                    flush = True
                else:
                    flush = False
            
            well = self.upload_plates_table.item(row, 1).text()
            compound_id = self.upload_plates_table.item(row, 2).text()
            batch = self.upload_plates_table.item(row, 3).text()
            form = self.upload_plates_table.item(row, 4).text()
            conc = self.upload_plates_table.item(row, 5).text()
            volume = self.upload_plates_table.item(row, 6).text()

            data = [plate_id,
                    well,
                    compound_id,
                    batch,
                    form,
                    conc,
                    volume]
            status = False
            if flush is False:
                retVal, status = dbInterface.uploadWellInformation(self.token,
                                                            plate_id,
                                                            well,
                                                            compound_id,
                                                            batch,
                                                            form,
                                                            conc,
                                                            volume)
            if status is False:
                repopulate_data.append(data)
                logging.getLogger(self.mod_name).info(f"Failed with uploadWellInformation Plate: {plate_id} Well: {well} Error: {retVal}")
            iTickCount += 1
            if iTickCount == iTicks:
                progress += 1
                iTickCount = 0
                self.upload_pbar.setValue(progress)
        self.upload_pbar.setValue(100)
        
        QApplication.restoreOverrideCursor()
        self.populate_upload_table(repopulate_data, error=True)
        self.enable_upload()

    def upload_moldisplay(self, item):
        if (item is not None):
            batchId = self.upload_plates_table.item(item.row(), 3).text()
            if len(batchId) > 0:
                displayMolfile(self, batchId)
                return
        self.structure_lab.clear()

    def export_upload_data(self):
        export_table(self.upload_plates_table)

    def verify_merge_plate(self, plate_id, index):
        self.merge_status_lab.setText("")
        if plate_id == "":
            self.merge_datas[index] = None
            return -1, False

        pattern1 = '^[pP]{1}[0-9]{6}$'
        pattern2 = '^[mM]{1}[xX]{1}[0-9]{4}$'

        if not re.match(pattern1, plate_id):
            if not re.match(pattern2, plate_id):
                self.merge_datas[index] = None
                return -1, False
            else:
                plateType = 'MX'
        else:
            plateType = 'plate'

        try:
            r, status = dbInterface.verifyPlate(self.token, plate_id)
            res = json.loads(r)
            if status == 0:
                raise Exception
            self.plate_ids[index] = plate_id
            if plateType == 'plate':
                data, b = dbInterface.getPlate(self.token, plate_id)
            else:
                data, b = dbInterface.getRack(self.token, plate_id)
                
            self.merge_datas[index] = json.loads(data)

            if (index == 0) and (len(self.merge_datas[0])):
                return -1, False
            return res[0]['wells'], True
        except:
            self.merge_datas[index] = None
            return -1, False


    def check_merge_sizes(self):
        self.sizes_dict = {}
        for i in range(1, 5):
            s = self.size_arr[i]
            if s != -1:
                if f'{s}' in self.sizes_dict:
                    self.sizes_dict[f'{s}'].append(i)
                else:
                    self.sizes_dict[f'{s}'] = [i]
        if len(self.sizes_dict) < 1:
            self.dom_size = -1
            return False
        self.dom_size = int(max(self.sizes_dict,
            key = lambda x: len(self.sizes_dict[x])))
        
        if len(self.sizes_dict) == 1:
            return True
        else: 
            return False

    def color_boxes(self):
        if self.merge_volume_eb.text() == "":
            self.mark_merge_box(5, "mismatch")
        else:
            self.mark_merge_box(5, "good")
        pattern1 = '^[pP]{1}[0-9]{6}$'
        pattern2 = '^[mM]{1}[xX]{1}[0-9]{4}$'

        t0 = self.currentTexts[0]
        if ((not self.ok_arr[0]) and (self.size_arr[0] != -1)) or \
             ((t0 != "") and (not (re.match(pattern1, t0) or re.match(pattern2, t0)) )):
            self.mark_merge_box(0, "bad")
        elif (self.ok_arr[0] and all(c == False for c in self.ok_arr[1:])) \
             or ((self.dom_size != -1) and (self.dom_size*4 == self.size_arr[0])):
            self.mark_merge_box(0, "good")
        else:
            self.mark_merge_box(0, "mismatch")
        for i in range(1, 5):
            tx = self.currentTexts[i]
            if ((not self.ok_arr[i]) and (self.size_arr[i] != -1)) or \
                 ((tx != "") and (not (re.match(pattern1, tx) or re.match(pattern2, tx)) )):
                    self.mark_merge_box(i, "bad")
            elif (self.dom_size != -1) and\
                 (i in (self.sizes_dict[f'{self.dom_size}'])):
                self.mark_merge_box(i, "good")
            else:
                self.mark_merge_box(i, "mismatch")     

    def mark_merge_box(self, i, color):
        # sets dynamic property defined by QtDesigner in the .ui-file
        # setting "state" to "good", "bad", or "mismatch" changes stylesheet to different colors
        if i == 0:
            self.merge_frame_result.setProperty("state", color)
            self.merge_frame_result.style().polish(self.merge_frame_result)
        elif i == 1:
            self.merge_frame_1.setProperty("state", color)
            self.merge_frame_1.style().polish(self.merge_frame_1)
        elif i == 2:
            self.merge_frame_2.setProperty("state", color)
            self.merge_frame_2.style().polish(self.merge_frame_2)
        elif i == 3:
            self.merge_frame_3.setProperty("state", color)
            self.merge_frame_3.style().polish(self.merge_frame_3)
        elif i == 4:
            self.merge_frame_4.setProperty("state", color)
            self.merge_frame_4.style().polish(self.merge_frame_4)
        elif i == 5:
            self.merge_volume_eb.setProperty("state", color)
            self.merge_volume_eb.style().polish(self.merge_volume_eb)

    def check_fields_unique(self):
        ids = []
        for i in range(0, 5):
            if self.ok_arr[i]:
                if self.plate_ids[i] not in ids:
                    ids.append(self.plate_ids[i])
                else: 
                    self.ok_arr[i] = False
                    self.plate_ids[i] = -1

    def get_free_box_index(self, ok_list, mod):
        try:
            next_index = ok_list.index(False, mod)
            return next_index
        except ValueError:
            return 0

    def move_focus(self, mod, ok_list):
        if ok_list[mod] is True:
            next_box = self.get_free_box_index(ok_list, mod)
            if next_box == 0:
                self.join_result_eb.setFocus()
            elif next_box == 1:
                self.join_q1_eb.setFocus()
            elif next_box == 2:
                self.join_q2_eb.setFocus()
            elif next_box == 3:
                self.join_q3_eb.setFocus()
            elif next_box == 4:
                self.join_q4_eb.setFocus()

    def mod0(self):
        self.currentTexts[0] = self.join_result_eb.text()
        self.mod_arr[0] = 1
        self.merge_check(volume_was_modified=False)

    def mod1(self):
        self.currentTexts[1] = self.join_q1_eb.text()
        self.mod_arr[1] = 1
        self.merge_check(volume_was_modified=False)
    
    def mod2(self):
        self.currentTexts[2] = self.join_q2_eb.text()
        self.mod_arr[2] = 1
        self.merge_check(volume_was_modified=False)
    
    def mod3(self):
        self.currentTexts[3] = self.join_q3_eb.text()
        self.mod_arr[3] = 1
        self.merge_check(volume_was_modified=False)
    
    def mod4(self):
        self.currentTexts[4] = self.join_q4_eb.text()
        self.mod_arr[4] = 1
        self.merge_check(volume_was_modified=False)

    def mod_vol(self):
        self.currentTexts[5] = self.merge_volume_eb.text()
        self.merge_check(volume_was_modified=True)

#TODO retranslate OK plates to html
    def merge_check(self, volume_was_modified=True):
        noEmptyEntriesOK = (self.join_result_eb.text() != "") and \
            ((self.join_q1_eb.text() != "") or \
            (self.join_q2_eb.text() != "") or \
            (self.join_q3_eb.text() != "") or \
            (self.join_q4_eb.text() != "")) # at least one (1) q# and result is non-empty
        
        if self.mod_arr[1] != 0:
            self.size_arr[1], self.ok_arr[1] = \
                self.verify_merge_plate(self.join_q1_eb.text(), 1)
        if self.mod_arr[2] != 0:
            self.size_arr[2], self.ok_arr[2] = \
                self.verify_merge_plate(self.join_q2_eb.text(), 2)
        if self.mod_arr[3] != 0:
            self.size_arr[3], self.ok_arr[3] = \
                self.verify_merge_plate(self.join_q3_eb.text(), 3)
        if self.mod_arr[4] != 0:
            self.size_arr[4], self.ok_arr[4] = \
                self.verify_merge_plate(self.join_q4_eb.text(), 4)
        if self.mod_arr[0] != 0:
            self.size_arr[0], self.ok_arr[0] = \
                self.verify_merge_plate(self.join_result_eb.text(), 0)
        
        self.check_fields_unique()
        if volume_was_modified is False:
            mod = self.mod_arr.index(1)
            # move focus
            self.move_focus(mod, self.ok_arr)

        self.mod_arr = [0]*5

        fieldsFilledOK = \
            ((self.ok_arr[1] is True) or ((self.ok_arr[1] is False) and (self.size_arr[1] == -1))) and \
            ((self.ok_arr[2] is True) or ((self.ok_arr[2] is False) and (self.size_arr[2] == -1))) and \
            ((self.ok_arr[3] is True) or ((self.ok_arr[3] is False) and (self.size_arr[3] == -1))) and \
            ((self.ok_arr[4] is True) or ((self.ok_arr[4] is False) and (self.size_arr[4] == -1))) and \
            ((self.ok_arr[0] is True) or ((self.ok_arr[0] is False) and (self.size_arr[0] == -1)))
            # filled fields are valid

        sizesMatchingOK = self.check_merge_sizes()# sizes between parts match
        self.color_boxes()
        targetSizeOK = (self.size_arr[0] != -1) and \
            (self.dom_size*4 == self.size_arr[0]) # sizes match from parts to result, etc

        volumeOK = (self.merge_volume_eb.text() != "")
        
        if noEmptyEntriesOK and fieldsFilledOK and sizesMatchingOK and \
             targetSizeOK and volumeOK:
            self.nine6to384_btn.setEnabled(True)
            self.nine6to384_btn.setProperty("state", "good")
            self.nine6to384_btn.style().polish(self.nine6to384_btn)
        else:
            self.nine6to384_btn.setEnabled(False)
            self.nine6to384_btn.setProperty("state", "mismatch")
            self.nine6to384_btn.style().polish(self.nine6to384_btn)
        
        self.showMergePlates()

    def nine6to384_merge(self):
        r = None
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            r, status = dbInterface.mergePlates(self.token,
                                            self.join_q1_eb.text(),
                                            self.join_q2_eb.text(),
                                            self.join_q3_eb.text(),
                                            self.join_q4_eb.text(),
                                            self.join_result_eb.text(),
                                            self.merge_volume_eb.text())
            if not status:
                raise Exception
            merged_plates = ",".join([id for id in self.plate_ids[1:] if id != -1])
            
            merge = self.join_result_eb.text()
            self.join_result_eb.setText("")
            self.join_result_eb.setText(merge)

            self.merge_status_lab.setText(f"Merged plates [{merged_plates}] into \
{self.plate_ids[0]}.\nReturned message:\"{r}\"")

            QApplication.restoreOverrideCursor()
            return
        except:
            merged_plates = ",".join([id for id in self.plate_ids[1:] if id != -1])
            self.merge_status_lab.setText(f"Merging plates [{merged_plates}] into \
{self.plate_ids[0]} failed with error message:\"{r}\"")
            self.ok_arr[0] = False
            self.merge_check()
            QApplication.restoreOverrideCursor()
            return
    
    def showMergePlates(self):
        def disp_tran(quad, data):
            shiftAlpha = 0
            shiftNum = 0
            if quad == 1:
                return data
            elif quad == 2:
                shiftNum = 12
            elif quad == 3:
                shiftAlpha = 8
            elif quad == 4:
                shiftAlpha = 8
                shiftNum = 12
            ret = []
            wellColName = 'well'
            try:
                if data[0]['well'] == data[0]['well']:
                    wellColName = 'well'
            except:
                wellColName = 'position'
            for well in data:
                new_well = well.copy()
                info = new_well[wellColName]
                row = chr(ord(info[0]) + shiftAlpha)
                col = int(info[1:]) + shiftNum
                new_well[wellColName] = f"{row}{col}"
                ret.append(new_well)
            return ret

        resultdata = self.merge_datas[0]
        data = []
        for i in range(1, 5):
            if self.merge_datas[i] != None:
                data.extend(disp_tran(i, self.merge_datas[i]))
        
        if not (all(x == False for x in self.ok_arr)):
            size = -1
            if self.dom_size == 96:
                size = 384
            elif self.dom_size == 384:
                size = 1536
            else: 
                # unrecognized size
                logging.getLogger(self.mod_name).error("attempting to display incorrectly sized plate")
                return
            self.plate_display.setHtml(plate_to_html(data, size, resultdata, size))
        return
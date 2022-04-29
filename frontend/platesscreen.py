import sys, os, logging, re, csv
from unittest import skip
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QIntValidator

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

        self.plates_tab_wg.setCurrentIndex(0)
        self.new_plates_comment_eb.setFocus()
        self.plates_tab_wg.currentChanged.connect(self.tabChanged)

        self.new_plates_save_btn.clicked.connect(self.createPlates)
        self.new_plates_save_btn.setEnabled(False)
        types = [' ', "96", "384", "1536"]
        self.new_plates_type_cb.addItems(types)
        self.new_plates_type_cb.currentTextChanged.connect(self.check_plates_input)
        self.new_plates_comment_eb.textChanged.connect(self.check_plates_input)

        self.plate_data = None
        self.plate_search_btn.clicked.connect(self.check_plate_search_input)
        self.plate_comment_btn.clicked.connect(self.editComment)
        self.plate_discard_btn.clicked.connect(self.discardPlate)
        self.setDiscard(False)
        self.plate_discard_chk.stateChanged.connect(self.readyDiscard)
        self.plate_export_btn.clicked.connect(self.plate_export_data)
        self.plate_print_btn.clicked.connect(self.printPlate)
        self.plate_print_btn.setEnabled(False)

        self.plate_table.currentItemChanged.connect(self.plate_moldisplay)

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
            elif self.plates_tab_wg.currentIndex() == 1:
                self.check_plate_search_input()
            else:
                return

    def tabChanged(self):
        page_index = self.plates_tab_wg.currentIndex()
        self.structure_lab.clear()
        if page_index == 0:
            self.new_plates_comment_eb.setFocus()
        elif page_index == 1:
            self.plate_search_eb.setFocus()
            self.plate_moldisplay(self.plate_table.currentItem())
        elif page_index == 2:
            self.choose_file_btn.setFocus()
            self.upload_moldisplay(self.upload_plates_table.currentItem())
        elif page_index == 3:
            self.join_q1_eb.setFocus()
            #self.move_focus(0, self.ok_arr)

    def check_plates_input(self):
        if (self.new_plates_type_cb.currentText() != ' ') and \
            (self.new_plates_comment_eb.text() != ""):
            self.new_plates_save_btn.setEnabled(True)
        else:
            self.new_plates_save_btn.setEnabled(False)

    def createPlates(self):
        type = self.new_plates_type_cb.currentText()
        name = self.new_plates_comment_eb.text()
        nr_o_ps = self.new_n_plates_sb.value()
        try:
            res, status = dbInterface.createPlates(self.token, type, name, nr_o_ps)
            if not status:
                raise Exception
            self.new_plates_res_lab.setText(res)
            self.new_plates_type_cb.setCurrentText(' ')
            self.new_plates_comment_eb.setText("")
            self.new_n_plates_sb.setValue(1)
        except:
            logging.getLogger(self.mod_name).info(f"create plates [{type}:{name}:{nr_o_ps}] failed:\n{res}")

    def check_plate_search_input(self):
        pattern = '^[pP]{1}[0-9]{6}$'
        t = re.sub("[^0-9a-zA-Z]+", " ", self.plate_search_eb.text())
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
        logging.getLogger(self.mod_name).info(f"plate search {plate}")
        res = dbInterface.getPlate(self.token, plate)
        try:
            self.plate_data = json.loads(res)
            if len(self.plate_data) < 1:
                raise Exception
            logging.getLogger(self.mod_name).info(f"received data")
            self.plate_comment_eb.setEnabled(True)
            self.plate_comment_btn.setEnabled(True)
            self.plate_comment_eb.setText(self.plate_data[0]['description'])
            self.setPlateTableData(self.plate_data)
            self.setDiscard(False)
            self.setDiscard(True)
            self.plate_print_btn.setEnabled(True)
        except:
            logging.getLogger(self.mod_name).info(f"no data received")
            self.plate_data = None
            self.plate_comment_eb.setText("")
            self.plate_comment_eb.setEnabled(False)
            self.plate_comment_btn.setEnabled(False)
            self.plate_table.setRowCount(0)
            self.plate_print_btn.setEnabled(False)        
    
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

    def editComment(self):
        new_comment = self.plate_comment_eb.text()
        plate = self.plate_search_eb.text()
        try:
            _, status = dbInterface.updatePlateName(self.token, plate, new_comment)
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

    def plate_moldisplay(self, item):
        if (item is not None):
            batchId = self.plate_table.item(item.row(), 2).text()
            if len(batchId) > 0:
                displayMolfile(self, batchId)
                return
        self.structure_lab.clear()


    def plate_export_data(self):
        export_table(self.plate_table)


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
                self.upload_file_btn.setEnabled(True)
                self.upload_pbar.setValue(0)
                self.upload_pbar.hide()
                data = list(reader)
                if has_header:
                    data.pop(0)
                self.populate_upload_table(data)
        except:
            self.upload_plates_data = None
            self.upload_file_btn.setEnabled(False)
            logging.getLogger(self.mod_name).error("plates file import failed")

    def populate_upload_table(self, data, error=False):
        self.upload_plates_table.setRowCount(0)
        self.upload_plates_table.setRowCount(len(data))
        # assume data like [{col1, col2, col3, ...}, {...}]
        try:
            for n in range(len(data)):
                for m in range(len(data[n])):
                    newItem = QTableWidgetItem(f"{data[n][m]}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    if error is True:
                        newItem.setBackground(QColor(250, 103, 92))
                    self.upload_plates_table.setItem(n, m, newItem)
                    for k in range(m, self.upload_plate_table.columnCount()):
                        # empty cells
                        newItem = QTableWidgetItem("")
                        newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                        newItem.setBackground(QColor(250, 103, 92))
                        self.upload_plates_table.setItem(n, m, newItem)
        except:
            logging.getLogger(self.mod_name).error("plate file import failed")

    def upload_plate_table(self):
        repopulate_data = []
        # set up progress bar
        iTickCount = 0
        iTicks = int(self.upload_plates_table.rowCount() / 100)
        progress = 0
        self.upload_pbar.setValue(progress)
        self.upload_pbar.show()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        for row in range(self.upload_plates_table.rowCount()):
            plate_id = self.upload_plates_table.item(row, 0).text()
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
            _, status = dbInterface.uploadWellInformation(self.token,
                                                          plate_id,
                                                          well,
                                                          compound_id,
                                                          batch,
                                                          form,
                                                          conc,
                                                          volume)
            if status is False:
                repopulate_data.append(data)
            else:
                iTickCount += 1
                if iTickCount == iTicks:
                    progress += 1
                    iTickCount = 0
                    self.upload_pbar.setValue(progress)
        self.upload_pbar.setValue(100)
        
        QApplication.restoreOverrideCursor()
        self.populate_upload_table(repopulate_data, error=True)

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
            return -1, False

        pattern1 = '^[pP]{1}[0-9]{6}$'
        pattern2 = '^[mM]{1}[xX]{1}[0-9]{4}$'
        if not (re.match(pattern1, plate_id) or\
                re.match(pattern2, plate_id)):
            return -1, False
            
        try:
            r, status = dbInterface.verifyPlate(self.token, plate_id)
            res = json.loads(r)
            if status == 0:
                raise Exception
            self.plate_ids[index] = plate_id
            return res[0]['wells'], True
        except:
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
            self.merge_status_lab.setText(f"Merged plates [{merged_plates}] into \
{self.plate_ids[0]}.\nReturned message:\"{r}\"")
            
            self.join_result_eb.setText("")
            self.join_q1_eb.setText("")
            self.join_q2_eb.setText("")
            self.join_q3_eb.setText("")
            self.join_q4_eb.setText("")

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

import sys, os, logging, re, csv
from unittest import skip
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

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

        self.new_plates_save_btn.clicked.connect(self.createPlates)
        self.new_plates_save_btn.setEnabled(False)
        types = [None, "96", "384", "1536"]
        self.new_plates_type_cb.addItems(types)
        self.new_plates_type_cb.currentTextChanged.connect(self.check_plates_input)
        self.new_plate_comment_eb.textChanged.connect(self.check_plates_input)

        self.plate_data = None
        self.plate_search_btn.clicked.connect(self.check_plate_search_input)
        self.plate_comment_btn.clicked.connect(self.editComment)
        self.setDiscard(False)
        self.plate_discard_chk.stateChanged.connect(self.readyDiscard)
        self.plate_export_btn.clicked.connect(self.plate_export_data)

        self.choose_file_btn.clicked.connect(self.import_plates_file)
        self.upload_file_btn.clicked.connect(self.upload_plate_table)
        self.upload_export_btn.clicked.connect(self.export_upload_data)
        self.upload_pbar.setValue(0)
        self.upload_pbar.hide()

        #self.merge_status_palette = {'good':QColor(167, 221, 181), 'bad':QColor(234, 112, 112), 'mismatch':QColor(154, 231, 244)}
        self.nine6to384_btn.clicked.connect(self.nine6to384_merge)
        self.nine6to384_btn.setEnabled(False)

        self.dom_size = -1
        self.mod_arr = [0]*5 # i=0: result, i=1:q1, ...
        self.size_arr = [-1]*5 # i=0: result, i=1:q1, ...
        self.ok_arr = [False]*5 # i=0: result, i=1:q1, ...

        self.join_q1_eb.textChanged.connect(self.mod1)
        self.join_q2_eb.textChanged.connect(self.mod2)
        self.join_q3_eb.textChanged.connect(self.mod3)
        self.join_q4_eb.textChanged.connect(self.mod4)
        self.join_result_eb.textChanged.connect(self.mod0)

        #self.join_q1_eb.textChanged.connect(self.merge_check)
        #self.join_q2_eb.textChanged.connect(self.merge_check)
        #self.join_q3_eb.textChanged.connect(self.merge_check)
        #self.join_q4_eb.textChanged.connect(self.merge_check)
        #self.join_result_eb.textChanged.connect(self.merge_check)
        


    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            if self.plates_tab_wg.currentIndex() == 0:
                # press button
                return
            elif self.plates_tab_wg.currentIndex() == 1:
                self.check_plate_search_input()
            else: # index = 1
                # maybe not?
                return

    def tabChanged(self):
        page_index = self.plates_tab_wg.currentIndex()
        if page_index == 0:
            return
        elif page_index == 1:
            return
        elif page_index == 2:
            return

    def check_plates_input(self):
        if (self.new_plates_type_cb.currentText() != "") and \
            (self.new_plate_comment_eb.text() != ""):
            self.new_plates_save_btn.setEnabled(True)
        else:
            self.new_plates_save_btn.setEnabled(False)

    def createPlates(self):
        type = self.new_plates_type_cb.currentText()
        name = self.new_plate_comment_eb.text()
        nr_o_ps = self.new_n_plates_sb.value()
        try:
            res, status = dbInterface.createPlates(self.token, type, name, nr_o_ps)
            if not status:
                raise Exception
            self.new_plates_res_lab.setText(res)
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
            self.setDiscard(False)

    def plateSearch(self, plate):
        if len(plate) < 1:
            return
        logging.getLogger(self.mod_name).info(f"plate search {plate}")
        res = dbInterface.getPlate(self.token, plate)
        try:
            self.plate_data = json.loads(res)
            logging.getLogger(self.mod_name).info(f"received data")
            print(self.plate_data)
            if len(self.plate_data) < 1:
                raise Exception
            self.plate_comment_eb.setEnabled(True)
            self.plate_comment_btn.setEnabled(True)
            self.plate_comment_eb.setText(self.plate_data[0]['description'])
            self.setPlateTableData(self.plate_data)
            self.setDiscard(False)
            self.setDiscard(True)
        except:
            self.plate_data = None
            self.plate_comment_eb.setText("")
            self.plate_comment_eb.setEnabled(False)
            self.plate_comment_btn.setEnabled(False)
            self.plate_table.setRowCount(0)          
    
    def setPlateTableData(self, data):
        self.plate_table.setRowCount(0)
        self.plate_table.setRowCount(len(data))
        for n in range(len(data)):
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
            self.plate_table.setItem(n, 4, newItem)

    def editComment(self):
        new_comment = self.plate_comment_eb.text()
        plate = self.plate_search_eb.text()
        #try:
        _, status = dbInterface.updatePlateName(self.token, plate, new_comment)
            #if status is False:
            #    raise Exception
        #except:
        #    logging.getLogger(self.mod_name).info(f"updating comment failed")
        self.check_plate_search_input()

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
                #print(data[n])
                for m in range(len(data[n])):
                    newItem = QTableWidgetItem(f"{data[n][m]}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    if error is True:
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

    def export_upload_data(self):
        export_table(self.upload_plates_table)


    def verify_merge_plate(self, plate_id):
        if plate_id == "":
            return -1, True
        try:
            r, status = dbInterface.verifyPlate(self.token, plate_id)
            res = json.loads(r)
            if status == 0:
                raise Exception
            return res[0]['wells'], True
        except:
            print("except")
            return -1, False

    def check_merge_sizes(self):
        self.sizes_dict = {}
        for i, s in enumerate(self.size_arr[1:]):
            if s != -1:
                if f'{s}' in self.sizes_dict:
                    self.sizes_dict[f'{s}'].append(i)
                else:
                    self.sizes_dict[f'{s}'] = [i]
        if len(self.sizes_dict) < 1:
            self.dom_size = -1
            return
        self.dom_size = int(max(self.sizes_dict, key = lambda x: len(self.sizes_dict[x])))
        for i in range(len(self.size_arr[1:])):
            if i in (self.sizes_dict[f'{self.dom_size}']):
                self.mark_merge_box(i, "good")#self.merge_status_palette['good'])
            else: 
                if self.size_arr[i] != -1:
                    self.mark_merge_box(i, "mismatch")#self.merge_status_palette['mismatch'])
                else:
                    self.mark_merge_box(i, "bad")#self.merge_status_palette['bad'])
        if len(self.sizes_dict) == 1:
            return True
        else: 
            return False

    def mark_merge_box(self, i, color):
        if i == 0:
            self.merge_frame_result.setProperty("state", color)#setBackground(color)
            self.merge_frame_result.update()
        elif i == 1:
            self.merge_frame_1.setProperty("state", color)#setBackground(color)
            self.merge_frame_1.update()
        elif i == 2:
            self.merge_frame_2.setProperty("state", color)#setBackground(color)
            self.merge_frame_2.update()
        elif i == 3:
            self.merge_frame_3.setProperty("state", color)#setBackground(color)
            self.merge_frame_3.update()
        elif i == 4:
            self.merge_frame_4.setProperty("state", color)#setBackground(color)
            self.merge_frame_4.update()

    def mod0(self):
        self.mod_arr[0] = 1
        self.merge_check()

    def mod1(self):
        self.mod_arr[1] = 1
        self.merge_check()
    
    def mod2(self):
        self.mod_arr[2] = 1
        self.merge_check()
    
    def mod3(self):
        self.mod_arr[3] = 1
        self.merge_check()
    
    def mod4(self):
        self.mod_arr[4] = 1
        self.merge_check()

    def merge_check(self):
        self.debugprint("before")
        cond1 = (self.join_result_eb.text() != "") and \
            ((self.join_q1_eb.text() != "") or \
            (self.join_q2_eb.text() != "") or \
            (self.join_q3_eb.text() != "") or \
            (self.join_q4_eb.text() != "")) # at least one (1) q# and result is non-empty
        
        if self.mod_arr[1] != 0:
            self.size_arr[1], self.ok_arr[1] = self.verify_merge_plate(self.join_q1_eb.text())
            self.mod_arr[1] = 0
        if self.mod_arr[2] != 0:
            self.size_arr[2], self.ok_arr[2] = self.verify_merge_plate(self.join_q2_eb.text())
            self.mod_arr[2] = 0
        if self.mod_arr[3] != 0:
            self.size_arr[3], self.ok_arr[3] = self.verify_merge_plate(self.join_q3_eb.text())
            self.mod_arr[3] = 0
        if self.mod_arr[4] != 0:
            self.size_arr[4], self.ok_arr[4] = self.verify_merge_plate(self.join_q4_eb.text())
            self.mod_arr[4] = 0
        if self.mod_arr[0] != 0:
            self.size_arr[0], self.ok_arr[0] = self.verify_merge_plate(self.join_result_eb.text())
            if self.ok_arr[0]:
                self.mark_merge_box(0, "good")#self.merge_status_palette['good'])
            else:
                self.mark_merge_box(0, "bad")#self.merge_status_palette['bad'])
            self.mod_arr[0] = 0
        
        cond2 = self.ok_arr[1] and \
                self.ok_arr[2] and \
                self.ok_arr[3] and \
                self.ok_arr[4] and \
                self.ok_arr[0]# filled fields are valid

        cond3 = self.check_merge_sizes()# sizes between parts match
        cond4 = (self.size_arr[0] != -1) and (self.dom_size*4 == self.size_arr[0]) # sizes match from parts to result, etc

        if cond1 and cond2 and cond3 and cond4:
            self.nine6to384_btn.setEnabled(True)
            self.nine6to384_btn.setProperty("state", "good")#self.merge_status_palette['good'])
        else:
            self.nine6to384_btn.setEnabled(False)
            self.nine6to384_btn.setProperty("state", "mismatch")#self.merge_status_palette['mismatch'])
        self.debugprint("after")

    def debugprint(self, i):
        print(i)
        print(f"dom_size: {self.dom_size}")
        print(f"mod_arr:  {self.mod_arr}" )
        print(f"size_arr: {self.size_arr}")
        print(f"ok_arr:   {self.ok_arr}")

    def nine6to384_merge(self):
        print("MERGING")

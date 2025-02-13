import re, sys, os, logging
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog, QListWidget, QDialog
from PyQt5.QtCore import Qt

from myList import MyListClass

import math
import numpy as np
from numpy import random as rng
import networkx as nx

from cellolib import *

class SearchScreen(QMainWindow):
    from cellolib import gotoVials, gotoBoxes, gotoMicrotubes, gotoPlates
    def __init__(self, token, test):
        super(SearchScreen, self).__init__()
        self.token = token
        self.mod_name = "search"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/searchwindow.ui"), self)

        self.centralwidget.setProperty("test", test)

        self.goto_vials_btn.clicked.connect(self.gotoVials)
        self.goto_boxes_btn.clicked.connect(self.gotoBoxes)
        self.goto_microtubes_btn.clicked.connect(self.gotoMicrotubes)
        self.goto_plates_btn.clicked.connect(self.gotoPlates)

        self.search_tab_wg.setCurrentIndex(0)
        self.search_tab_wg.currentChanged.connect(self.tabChanged)

        self.multvial_export_btn.clicked.connect(self.export_multvial_table)
        self.multvial_export_btn.setEnabled(False)
        self.multvial_table.currentItemChanged.connect(self.multvial_moldisplay)

        self.mult_vial_search_btn.clicked.connect(self.search_many_vials)

        self.batch_search_btn.clicked.connect(self.search_batches)
        self.batch_export_btn.clicked.connect(self.export_batch_table)
        self.show_plates_cb.setChecked(True)
        self.show_microtubes_cb.setChecked(False)
        self.show_vials_cb.setChecked(False)

        self.batch_export_btn.setEnabled(False)
        self.batch_table.currentItemChanged.connect(self.batch_moldisplay)

        self.v_search = False
        self.vial_search_eb.textChanged.connect(self.check_vial_search_input)

        self.discard_vial_btn.clicked.connect(self.discardVial)
        self.print_label_btn.clicked.connect(self.printLabel)
        self.discard_vial_btn.setEnabled(False)
        self.print_label_btn.setEnabled(False)

        self.pool_input_btn.clicked.connect(self.open_batchids_file)
        self.pool_gen_btn.clicked.connect(self.generate_pool_scheme)
        self.pool_gen_btn.setEnabled(False)

        self.pool_scheme_to_cb_btn.clicked.connect(self.scheme_to_clipboard)
        self.pool_scheme_to_file_btn.clicked.connect(self.scheme_to_file)

        self.searchBatchesInPlates_btn.clicked.connect(self.searchBatchesInPlates)
        self.copyBatchesInPlates_btn.clicked.connect(self.copyBatchesInPlates)

        self.createPlateList_btn.clicked.connect(self.createPlateList)
        self.platesList.setSelectionMode(QListWidget.SingleSelection)
        self.editPlateList_btn.clicked.connect(self.editPlateList)
        self.deletePlateList_btn.clicked.connect(self.deletePlateList)
        
        self.createBatchList_btn.clicked.connect(self.createBatchList)
        self.batchesList.setSelectionMode(QListWidget.SingleSelection)
        self.editBatchList_btn.clicked.connect(self.editBatchList)
        self.deleteBatchList_btn.clicked.connect(self.deleteBatchList)
        
    # capture certain keypresses in certain tabs
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            if self.search_tab_wg.currentIndex() == 1:
                self.search_many_vials()
                return
            elif self.search_tab_wg.currentIndex() == 2:
                self.search_batches()
                return
            else:
                return

    # set focus and do visual housekeeping
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


    def check_vial_search_input(self):
        pattern =r'^[vV]\d{6,7}$'
        t = self.vial_search_eb.text()
        t = t.rstrip()
        if re.match(pattern, t):
            self.searchVial(t)
        else:
            self.discard_vial_btn.setEnabled(False)
            self.print_label_btn.setEnabled(False)

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
            self.structure_lab.clear()
            self.discard_vial_btn.setEnabled(False)
            self.print_label_btn.setEnabled(False)
            logging.getLogger(self.mod_name).info(f"vial search for {vialId} returned: {res}")
            return
        logging.getLogger(self.mod_name).info(f"receieved {self.vial_data}")
        self.v_search = True
        self.errorlabel.setText('')
        self.onevial_batch_eb.setText(f"{self.vial_data[0]['batch_id']}")
        self.onevial_compound_id_eb.setText(f"{self.vial_data[0]['compound_id']}")
        self.onevial_box_loc_eb.setText(f"{self.vial_data[0]['box_id']}")
        self.onevial_coords_eb.setText(f"{self.vial_data[0]['coordinate']}")
        self.discard_vial_btn.setEnabled(True)
        self.print_label_btn.setEnabled(True)
        displayMolfile(self, vialId)


    def createPlateList(self):
        self.my_list_dialog = MyListClass(self)  # Pass self (MainWindow) as parent

        # Make dialog modal
        self.my_list_dialog.setModal(True)

        # Show the dialog and get the result (if needed)
        result = self.my_list_dialog.exec_()  # Returns QDialog.Accepted or QDialog.Rejected

        '''
        self.dialog = QDialog() # Create a dialog instance
        self.le = Ui_ListEdit()  # Create an instance of the UI class
        self.le.setupUi(self.dialog)  # Set up the UI on the dialog
        self.le.listType_cb.addItem("Batch Id")
        
        self.dialog.setModal(True)
        #self.dialog.setWindowTitle("List Edit")
        # Show the dialog
        self.dialog.exec_() # or self.dialog.show() if not modal

        '''
        self.platesList.addItem('Item')

    def editPlateList(self):
        pass

    def deletePlateList(self):
        selected_item = self.platesList.currentItem()
        if selected_item:
            row = self.platesList.row(selected_item)
            self.platesList.takeItem(row)



    def createBatchList(self):
        self.batchesList.addItem('Item')

    def editBatchList(self):
        pass

    def deleteBatchList(self):
        selected_item = self.batchesList.currentItem()
        if selected_item:
            row = self.batchesList.row(selected_item)
            self.batchesList.takeItem(row)


    
    def searchBatchesInPlates(self):
        pass

    def copyBatchesInPlates(self):
        pass


        
    def discardVial(self):
        vial = self.vial_search_eb.text()
        r = dbInterface.discardVial(self.token, vial)
        logging.getLogger(self.mod_name).info(f"discardVial [{vial}] returned: {r}")
        self.searchVial(vial)
        
    def printLabel(self):
        dbInterface.printVialLabel(self.token, self.vial_search_eb.text())
        
    def search_many_vials(self):
        vials = self.mult_vial_search_eb.text()
        vials = re.sub("[^0-9a-zA-Z-]+", " ", vials)
        logging.getLogger(self.mod_name).info(f"multvial search {vials}")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        v_n = len(vials.split(' '))
        if v_n > 5000:
            send_msg("Vial Search", f'Searching for {v_n} vials.\nThis might take a few minutes.\nPlease wait.\nPress OK.')
        res = dbInterface.getManyVials(self.token, vials)
        # change to get single vial at a time for progress bar TODO
        QApplication.restoreOverrideCursor()
        self.multvial_data = None
        try:
            self.multvial_data = json.loads(res)
        except:
            self.multvial_data = None
            self.multvial_export_btn.setEnabled(False)
            self.multvial_table.setRowCount(0)
            self.structure_lab.clear()
            logging.getLogger(self.mod_name).info(f"multvial search for {vials} returned: {res}")
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
                    self.multvial_table.setItem(n, 0, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['boxId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.multvial_table.setItem(n, 1, newItem)
                    for i in range(2, 8):
                        newItem = QTableWidgetItem("")
                        newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                        self.multvial_table.setItem(n, i, newItem)
                else:
                    newItem = QTableWidgetItem(f"{data[n]['vialId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.multvial_table.setItem(n, 0, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['boxId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    newItem.setToolTip(f"{data[n]['boxDescription']}")
                    self.multvial_table.setItem(n, 1, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['pos']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.multvial_table.setItem(n, 2, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['boxDescription']}")
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

                    newItem = QTableWidgetItem(f"{data[n]['dilution']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.multvial_table.setItem(n, 8, newItem)
                    
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
        self.batch_table.setRowCount(0)
        batches = self.batch_search_eb.text()
        batches = re.sub("[^0-9a-zA-Z_-]+", " ", batches)
        logging.getLogger(self.mod_name).info(f"batches search {batches}")

        vials_checked = 'yes' if self.show_vials_cb.isChecked() else 'no'
        tubes_checked = 'yes' if self.show_microtubes_cb.isChecked() else 'no'
        plates_checked = 'yes' if self.show_plates_cb.isChecked() else 'no'
        
        QApplication.setOverrideCursor(Qt.WaitCursor)

        accumulated_rows = []
        iAccumulator_count = 0
        iRowsBatch = 8
        self.popup = PopUpProgress(f'Searching...')
        self.popup.show()
        saBatches = batches.split()
        iNrOfRows = len(saBatches)
        iTick = 0
        rProgressSteps = (iRowsBatch/iNrOfRows)*100
        
        sAccuBatches = ''
        iCount = 0
        self.batches_data = []
        for batch in saBatches:
            iCount += 1
            sAccuBatches = sAccuBatches + ' ' + batch
            if iCount == iRowsBatch:
                res = dbInterface.getBatches(self.token, sAccuBatches, vials_checked, tubes_checked, plates_checked)

                newRows = json.loads(res)
                for nRow in newRows:
                    self.batches_data.append(nRow)
                iCount = 0
                sAccuBatches = ''
                iTick += rProgressSteps
                self.popup.obj.proc_counter(int(iTick))
                QApplication.processEvents()
        
        if sAccuBatches != '':
            res = dbInterface.getBatches(self.token, sAccuBatches, vials_checked, tubes_checked, plates_checked)
            newRows = json.loads(res)
            for nRow in newRows:
                self.batches_data.append(nRow)
                  
        self.popup.obj.proc_counter(100)
        self.popup.close()
        QApplication.restoreOverrideCursor()
        
        logging.getLogger(self.mod_name).info(f"receieved data")
        if len(self.batches_data) > 0:
            self.setBatchTableData(self.batches_data)
            self.batch_table.setCurrentCell(0,0)
            self.batch_export_btn.setEnabled(True)

    def setBatchTableData(self, data):
        self.batch_table.setRowCount(0)
        self.batch_table.setRowCount(len(data))
        self.batch_table.setSortingEnabled(False)

        keys = ["compound", "batch", "container", "pos", "conc", "loc", "name", "path"]
        # Convert list of tuples to list of dictionaries
        result = [dict(zip(keys, row)) for row in data]
        data = result
        # AC2239618 AG8135001 BJ1835001 CBK015588 CBK322493
        # EB_BY7184003 EB_CB1252001 EB_CC0517001 EB_CC0520001
        
        for n in range(len(data)):
            try:
                if f"{data[n]['batch']}" == "Not found":
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
                    newItem = QTableWidgetItem(f"{data[n]['compound']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.batch_table.setItem(n, 0, newItem)
                    
                    newItem = QTableWidgetItem(f"{data[n]['batch']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.batch_table.setItem(n, 1, newItem)
                    
                    newItem = QTableWidgetItem(f"{data[n]['container']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.batch_table.setItem(n, 2, newItem)
                    
                    newItem = QTableWidgetItem(f"{data[n]['pos']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    newItem.setToolTip(f"{data[n]['pos']}")
                    self.batch_table.setItem(n, 3, newItem)
                    
                    newItem = QTableWidgetItem(f"{data[n]['conc']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.batch_table.setItem(n, 4, newItem)
                    
                    newItem = QTableWidgetItem(f"{data[n]['loc']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.batch_table.setItem(n, 5, newItem)
                    
                    newItem = QTableWidgetItem(f"{data[n]['name']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.batch_table.setItem(n, 6, newItem)

                    newItem = QTableWidgetItem(f"{data[n]['path']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.batch_table.setItem(n, 7, newItem)

            except Exception as e:
                logging.error(str(e))
                logging.error(f"search for {data[n]['compound']} returned bad response: {data[n]}")
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


    def open_batchids_file(self):
        self.pool_ids_fname = QFileDialog.getOpenFileName(self, 'Choose File', 
                                                '.', "")
        self.pool_scheme_tb.setPlainText("")
        self.pool_status_lab.setText("")
        if self.pool_ids_fname[0] == '':
            self.pool_file_lab.setText("")
            self.pool_gen_btn.setEnabled(False)
            self.pool_scheme_to_cb_btn.setEnabled(False)
            self.pool_scheme_to_file_btn.setEnabled(False)
            return
        
        self.pool_file_lab.setText(self.pool_ids_fname[0])
        self.pool_gen_btn.setEnabled(True)
        self.pool_gen_btn.setFocus()

    # take a file/list of batch ids and generates a pooling scheme based on input parameters m & n
    def generate_pool_scheme(self):
        with open(self.pool_ids_fname[0], 'r') as f:
            batch_ids = f.readlines()
            batch_ids = (' '.join([batch_ids[i].strip() for i in range(len(batch_ids))])).split()

            #check duplicates
            singles = []
            duplicates = []
            for b in batch_ids:
                if b in singles:
                    duplicates.append(b)
                else:
                    singles.append(b)

            if len(duplicates) > 0:
                # There are duplicates
                uniques = '\n'.join(list(set(duplicates)))
                self.pool_status_lab.setText("Input file contains duplicates!\nThese batch ids have duplicates:")
                self.pool_scheme_tb.setPlainText(uniques)
                self.pool_gen_btn.setEnabled(False)
                return


            b_map = {i:batch_ids[i].strip() for i in range(len(batch_ids))}

            QApplication.setOverrideCursor(Qt.WaitCursor)

            # set spin threshold
            n=len(batch_ids)
            m=self.pool_m_sb.value()
            k=self.pool_k_sb.value()
            threshold = 100

            subs = np.empty(n, dtype=object)
            #init ids, occs left
            for id in range(n):
                subs[id] = [id, k]

            # init return list and neighbor graph
            wells = []
            G = nx.Graph()
            G.add_nodes_from([sub[0] for sub in subs])

            # INIT PBAR
            iTickInterval = 1
            if n > 100:
                iTickInterval = int(n / 100)
            self.popup = PopUpProgress(f'Generating pooling scheme for {n} batch IDs')
            self.popup.show()
            iTick = 0
            iLocalTick = 0

            subcount = 0
            spins = 0
            th_hit = 0
            reshuffles = 0 #
            # run until empty
            while subs.size > 0:
                iLocalTick += 1
                if iLocalTick == iTickInterval:
                    iLocalTick = 0
                    iTick += 1

                QApplication.processEvents()
                self.popup.obj.proc_counter(iTick)

                w = []
                del_list = []
                loops = 0
                # randomly select substances and check if they can be put in current well
                for m_i in range(min(m, len(subs))):
                    subcount += 1
                    found = False # get sub
                    while not found:
                        spins += 1
                        if (loops > threshold):
                            th_hit += 1
                            found = True
                            continue
                        if subs.size == 0:
                            found = True
                            continue
                        index = rng.choice(np.arange(subs.size)) # choose index
                        loops += 1
                        s = subs[index] # get tuple
                        id = s[0]
                        num = s[1]
                        if self.put_ok(G, w, s[0]) and (s[1] > 0): # check if chosen tup has no edges to subs already "in well"
                            # also check if it should occur again
                            w.append((s[0])) # append id and desc in a tuple to w
                            num = num - 1 # decrement
                            subs[index][1] = num # put value
                            if num == 0: # should be deleted
                                del_list.append(index)
                            found = True
                    loops = 0
                

                wells.append(w) # commit well
                for i in range(len(w) - 1):
                    for j in range(i + 1, len(w)):
                        G.add_edge(w[i], w[j])
                
                subs = np.delete(subs, del_list)

                # UPDATE PBAR # pbar.update()
                QApplication.processEvents()

                if len(wells) > int(math.ceil((k/m)*n)) or \
                    (len(wells) > k and (len(wells[-1]) < m and len(wells[-2]) < m)):
                    reshuffles += 1
                    extra = len(wells) - int(math.ceil((k/m)*n))
                    # redo extra + m*reshuffles finished wells
                    put_back = wells[-(extra + (m*reshuffles)):]
                    wells = wells[:-(extra + (m*reshuffles))]
                    for well in put_back:
                        for i in range(len(well) - 1):
                            for j in range(i + 1, len(well)):
                                G.remove_edge(well[i], well[j])
                        subs = self.add_to_subs(subs, well)
                    self.popup.obj.proc_counter(iTick)
                

            # CLOSE PBAR # pbar.close()
            QApplication.restoreOverrideCursor()
            self.popup.obj.proc_counter(100)
            self.popup.close()

            # to csv
            out = self.divider(wells, lambda x: b_map[x])
            self.pool_scheme = (''.join(out)).strip()
            self.pool_scheme_tb.setPlainText(self.pool_scheme)

            # set save buttons
            self.pool_scheme_to_cb_btn.setEnabled(True)
            self.pool_scheme_to_file_btn.setEnabled(True)

    def put_ok(self, G, w, id):
        ids = [sub for sub in w]
        if all(id not in G[i] for i in ids) and (id not in ids):
            return True
        else:
            return False

    def add_to_subs(self, subs, well):
        add = []
        for well_sub in well:
            index = -1
            if len(subs) > 0:
                for i in range(len(subs)):
                    sub = subs[i]
                    if sub[0] == well_sub:
                        index = i
            if index != -1:
                subs[index][1] = subs[index][1] + 1
            else: # re-add substance
                add.append([well_sub, 1])
        
        for s in add:
            subs = np.append(subs, np.empty(1, dtype=object))
            subs[-1] = s
        return subs

    def i_to_coord(self, index):
        return f"{chr(ord('A') + (index // 22))}{str((index % 22) + 1).zfill(2)}"

    def to_csv(self, num, wells, map):
        tl = map
        if map == None:
            tl = str
        ret = []
        for w_i in range(len(wells)):
            w = wells[w_i]
            w_s = ",".join([tl(i) for i in w])
            ret.append(f"{num},{self.i_to_coord(w_i)},{w_s}\n")
        return ret

    #returns csv string of 
    def divider(self, wells, id_map):
        out = []
        plate = 1
        while len(wells) > 0:
            buf = wells[:352]
            if len(wells) > 352:
                wells = wells[352:]
            else:
                wells = []
            out.extend(self.to_csv(plate, buf, id_map))
            plate += 1
        return out

    def scheme_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.pool_scheme_tb.toPlainText())
        return
    
    def scheme_to_file(self):
        fname = QFileDialog.getSaveFileName(self, 'Save to File', '.', "")
        if fname[0] == '':
            return
        with open(fname[0], "w") as f:
            f.write(self.pool_scheme_tb.toPlainText())
        logging.getLogger(self.mod_name).info(f"wrote to file: {fname[0]}")
        return

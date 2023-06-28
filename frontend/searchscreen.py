import re, sys, os, logging
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog
from PyQt5.QtCore import Qt

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
        #self.window().setWindowTitle("Search")

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


    def check_vial_search_input(self):
        pattern = '^[vV][0-9]{6}$'
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

    def discardVial(self):
        vial = self.vial_search_eb.text()
        r = dbInterface.discardVial(self.token, vial)
        logging.getLogger(self.mod_name).info(f"discardVial [{vial}] returned: {r}")
        self.searchVial(vial)
        
    def printLabel(self):
        dbInterface.printVialLabel(self.token, self.vial_search_eb.text())
        
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
        logging.getLogger(self.mod_name).info(f"receieved data")
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
                    newItem = QTableWidgetItem(f"{data[n]['boxId']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    newItem.setToolTip(f"{data[n]['boxDescription']}")
                    self.batch_table.setItem(n, 1, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['pos']}")
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.batch_table.setItem(n, 2, newItem)
                    newItem = QTableWidgetItem(f"{data[n]['boxDescription']}")
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
            except Exception as e:
                logging.error(str(e))
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

            # init return list and nieghbor graph
            wells = []
            G = nx.Graph()
            G.add_nodes_from([sub[0] for sub in subs])

            # INIT PBAR # pbar = tqdm(total=int((k/m)*n))
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
                            #print(f"hit threshold, subs left: {subs.size}")
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
                    #print(f"reshuffle #: {reshuffles}")
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
        ids = [sub for sub in w]#[sub[0] for sub in w]
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

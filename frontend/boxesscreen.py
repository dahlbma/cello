import sys, os, logging, re
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from cellolib import *

class BoxesScreen(QMainWindow):
    def __init__(self, token):
        super(BoxesScreen, self).__init__()
        self.token = token
        self.mod_name = "boxes"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/boxeswindow.ui"), self)
        self.window().setWindowTitle("Boxes")

        self.goto_search_btn.clicked.connect(self.gotoSearch)
        self.goto_vials_btn.clicked.connect(self.gotoVials)
        
        self.boxes_tab_wg.setCurrentIndex(0)
        self.boxes_tab_wg.currentChanged.connect(self.tabChanged)

        locations = [None, "Place 1", "Place 2", "Place 3"]
        self.add_location_cb.addItems(locations)
        types = [None, "10mM", "50mM", "Solid", "2mM", "20mM"]
        self.add_box_type_cb.addItems(types)
        self.add_box_btn.clicked.connect(self.addBox)
        self.add_box_btn.setEnabled(False)

        self.add_location_cb.currentTextChanged.connect(self.check_addbox_input)
        self.add_box_type_cb.currentTextChanged.connect(self.check_addbox_input)
        self.add_description_eb.textChanged.connect(self.check_addbox_input)

        self.update_box_eb.textChanged.connect(self.check_search_input)
        self.update_print_btn.clicked.connect(self.printLabel)
        self.update_print_btn.setEnabled(False)
        self.transit_vials_btn.clicked.connect(self.transitVials)
        self.transit_vials_btn.setEnabled(False)
        self.update_export_btn.clicked.connect(self.export_box_table)
        
        self.box_table.itemChanged.connect(self.updateVialPosition)
        self.box_table.currentItemChanged.connect(self.box_moldisplay)

        self.freebox_table.cellDoubleClicked.connect(self.showFreeBox)
        self.freebox_export_btn.clicked.connect(self.export_freebox_table)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            if self.boxes_tab_wg.currentIndex() == 0:
                # press button
                return
            else: # index = 1
                # maybe not?
                return

    def tabChanged(self):
        page_index = self.boxes_tab_wg.currentIndex()
        if page_index == 0:
            self.add_location_cb.setFocus()
            self.structure_lab.clear()
        elif page_index == 1:
            self.update_box_eb.setFocus()
            self.box_moldisplay(self.box_table.currentItem())
        elif page_index == 2:
            self.freebox_table.setFocus()
            self.structure_lab.clear()
            self.fetch_free_boxes()
            
    def gotoSearch(self):
        from searchscreen import SearchScreen
        resize_window(self)
        search = SearchScreen(self.token)
        self.window().addWidget(search)
        self.window().setCurrentIndex(self.window().currentIndex() + 1)
        search.vial_search_eb.setFocus()

    def gotoVials(self):
        from vialsscreen import VialsScreen
        resize_window(self)
        vials = VialsScreen(self.token)
        self.window().addWidget(vials)
        self.window().setCurrentIndex(self.window().currentIndex() + 1)
        vials.edit_vial_id_eb.setFocus()

    
    def addBox(self):
        print("add box")
        #validate description?
        #confirm message?
        return

    def check_addbox_input(self):
        if (self.add_location_cb.currentText()) != "" and \
            (self.add_box_type_cb.currentText() != "") and \
            (self.add_description_eb.text() != ""):
            self.add_box_btn.setEnabled(True)
        else:
            self.add_box_btn.setEnabled(False)

    def check_search_input(self):
        pattern = '^[a-zA-Z]{2}[0-9]{5}$'
        t = re.sub("[^0-9a-zA-Z]+", " ", self.update_box_eb.text())
        if re.match(pattern, t):
            self.search_for_box(t)
        else:
            #no match
            self.box_search = None
            self.box_table.setRowCount(0)


    def search_for_box(self, box):
        logging.getLogger(self.mod_name).info(f"box search {box}")
        self.box_search = box
        res = dbInterface.getBox(self.token, box)
        try:
            res = res.replace("null", "\"\"")
            self.box_data = json.loads(res)
            logging.getLogger(self.mod_name).info(f"recieved data")#: {self.box_data}")
        except:
            self.box_data = None
    
        #if (self.box_data is None) or (len(self.box_data) == 0):
        #    self.box_data = None
        #    self.path_js = None
        #    self.update_print_btn.setEnabled(False)
        #    self.box_table.setRowCount(0)
        #    self.update_name_lab.setText("Box not found!")
        #    self.update_name_lab.setStyleSheet("background-color: red")
        #    return
    
        path_res = dbInterface.getBoxLocation(self.token, box)
        logging.getLogger(self.mod_name).info(f"recieved path: {path_res}")
        self.path_js = json.loads(path_res)

        if (len(self.path_js) == 0) or (len(self.box_data) == 0) or (self.box_data is None):
            # bad results
            self.box_data = None
            self.path_js = None
            self.update_print_btn.setEnabled(False)
            self.transit_vials_btn.setEnabled(False)
            self.update_export_btn.setEnabled(False)
            self.box_table.setRowCount(0)
            self.structure_lab.clear()
            self.update_name_lab.setText("Box not found!")
            self.update_name_lab.setStyleSheet("background-color: red")
            return
        # not bad results
        self.update_name_lab.setText(f"{self.path_js[0]['path']}")
        self.update_name_lab.setStyleSheet("")
        self.setBoxTableData(self.box_data, box)
        self.box_table.setCurrentCell(0,0)
        self.update_print_btn.setEnabled(True)
        self.transit_vials_btn.setEnabled(True)
        self.update_export_btn.setEnabled(True)

    def setBoxTableData(self, data, box):
        self.box_table.itemChanged.disconnect()
        self.box_table.setRowCount(0)
        self.box_table.setRowCount(len(data))
        self.box_table.setSortingEnabled(False)
        for n in range(len(data)):
            try:
                newItem = QTableWidgetItem(f"{data[n]['vial_id']}")
                if len(newItem.text()) != 0:
                    newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                self.box_table.setItem(n, 0, newItem)
                newItem = QTableWidgetItem(f"{data[n]['batch_id']}")
                newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                self.box_table.setItem(n, 1, newItem)
                newItem = QTableWidgetItem(f"{data[n]['compound_id']}")
                newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                self.box_table.setItem(n, 2, newItem)
                newItem = QTableWidgetItem(f"{data[n]['coordinate']}")
                newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                self.box_table.setItem(n, 3, newItem)
                for m in range(self.box_table.columnCount()):
                    if len(self.box_table.item(n, m).text()) == 0:
                        self.box_table.item(n, m).setBackground(QColor(63, 186, 120))
            except:
                logging.error(f"search for {box} returned bad response: {data[n]}")
        self.box_table.setSortingEnabled(True)
        self.box_table.itemChanged.connect(self.updateVialPosition)
        return

    def updateVialPosition(self, item):
        row = item.row()
        col = item.column()
        vial = item.text()
        box = self.box_search
        pos = self.box_table.item(row, 3).text()

        logging.getLogger(self.mod_name).info(f"update {vial} position to {box}/{pos}")
        r = dbInterface.updateVialPosition(self.token, vial, box, pos)

        self.search_for_box(box)
        self.box_table.setCurrentCell(row, col)
        return

    def transitVials(self):
        items = self.box_table.selectedItems()
        vialList = []
        for it in items:
            if (it.column() == 0) and (len(it.text()) != 0):
                vialList.append(it.text())
        vials = " ".join(vialList)

        logging.getLogger(self.mod_name).info(f"send vials: {vials} to transit")
        r = dbInterface.transitVials(self.token, vials)

        self.search_for_box(self.box_search)
        return

    def box_moldisplay(self, item):
        if (item is not None) and (len(self.box_table.selectedItems()) == 1):
            #blank
            vialId = self.box_table.item(item.row(), 0).text()
            if len(vialId) > 0:
                displayMolfile(self, vialId)
                return
        self.structure_lab.clear()



    def printLabel(self):
        sBox = self.update_box_eb.text()
        dbInterface.printBoxLabel(self.token, sBox)
        return
    
    def export_box_table(self):
        export_table(self.box_table)


    def fetch_free_boxes(self):
        r = dbInterface.getFreePositions(self.token)
        try:
            self.freebox_data = json.loads(r)
        except:
            self.freebox_data = None
            self.freebox_export_btn.setEnabled(False)
        self.setFreeBoxesTableData(self.freebox_data)
        self.freebox_table.setCurrentCell(0,0)
        self.freebox_export_btn.setEnabled(True)
        return
    
    def setFreeBoxesTableData(self, data):
        self.freebox_table.setRowCount(0)
        if data is None:
            return
        self.freebox_table.setRowCount(len(data))
        self.freebox_table.setSortingEnabled(False)
        print(data[0])
        try:
            for n in range(len(data)):
                newItem = QCustomTableWidgetItem(f"{data[n]['free_positions']}")
                newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                self.freebox_table.setItem(n, 0, newItem)
                newItem = QTableWidgetItem(f"{data[n]['path']}")
                newItem.setToolTip(f"{data[n]['location']}")
                newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                self.freebox_table.setItem(n, 1, newItem)
                newItem = QTableWidgetItem(f"{data[n]['path']}")
                newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                self.freebox_table.setItem(n, 2, newItem)
        except:
            logging.error("bad response from freeBoxes")
        self.freebox_table.setSortingEnabled(True)
        return

    def showFreeBox(self, row, col):
        box = self.freebox_table.item(row, 1)
        if box.toolTip() != "":
            self.update_box_eb.setText(box.toolTip())
            self.boxes_tab_wg.setCurrentIndex(1)

    def export_freebox_table(self):
        export_table(self.freebox_table)

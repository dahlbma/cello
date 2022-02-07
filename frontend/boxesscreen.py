import sys, os, logging, re
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem

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
        
        self.boxes_tab_wg.setCurrentIndex(0)
        self.boxes_tab_wg.currentChanged.connect(self.tabChanged)

        types = [None, "10mM", "50mM", "Solid", "2mM", "20mM"]
        self.add_type_cb.addItems(types)
        self.add_box_btn.clicked.connect(self.addBox)

        self.update_box_eb.textChanged.connect(self.check_search_input)
        self.update_print_btn.clicked.connect(self.printLabel)
        self.update_print_btn.setEnabled(False)

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
            print("page 0")
        elif page_index == 1:
            print("page 1")

    def gotoSearch(self):
        from searchscreen import SearchScreen
        resize_window(self)
        search = SearchScreen(self.token)
        self.window().addWidget(search)
        self.window().setCurrentIndex(self.window().currentIndex() + 1)
        search.vial_search_eb.setFocus()

    
    def addBox(self):
        #validate description?
        #confirm message?
        return


    def check_search_input(self):
        pattern = '^[a-zA-Z]{2}[0-9]{5}$'
        t = re.sub("[^0-9a-zA-Z]+", " ", self.update_box_eb.text())
        if re.match(pattern, t):
            self.search_for_box(t)

    def search_for_box(self, box):
        logging.info(f"box search {box}")
        res = dbInterface.getBox(self.token, box)
        try:
            self.box_data = json.loads(res)
        except:
            self.box_data = None
        if len(self.box_data) == 0:
            self.box_data = None
            self.update_print_btn.setEnabled(False)
            self.box_table.setRowCount(0)
            self.update_name_lab.setText("Box not found!")
            self.update_name_lab.setStyleSheet("background-color: red")
            return
        logging.info(f"recieved {self.box_data}, GET path")
        path_res = dbInterface.getBoxLocation(self.token, box)
        logging.info(f"recieved {path_res}")
        path_js = json.loads(path_res)
        self.update_name_lab.setText(f"{path_js[0]['path']}")
        self.update_name_lab.setStyleSheet("")
        self.setBoxTableData(self.box_data, box)
        self.box_table.setCurrentCell(0,0)
        self.update_print_btn.setEnabled(True)

    def setBoxTableData(self, data, box):
        self.box_table.setRowCount(0)
        self.box_table.setRowCount(len(data))
        for n in range(len(data)):
            try:
                newItem = QTableWidgetItem(f"{data[n]['vial_id']}")
                self.box_table.setItem(n, 0, newItem)
                newItem = QTableWidgetItem(f"{data[n]['batch_id']}")
                self.box_table.setItem(n, 1, newItem)
                newItem = QTableWidgetItem(f"{data[n]['compound_id']}")
                self.box_table.setItem(n, 2, newItem)
                newItem = QTableWidgetItem(f"{data[n]['coordinate']}")
                self.box_table.setItem(n, 3, newItem)
            except:
                logging.error(f"search for {box} returned bad response: {data[n]}")
        return

    def printLabel(self):
        return
    

    def fetch_all_boxes(self):
        self.all_boxes = None
        return
    
    def setAllBoxesTableData(self, data):
        return

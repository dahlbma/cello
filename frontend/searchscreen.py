import re, sys, os, logging
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem

from cellolib import *

class SearchScreen(QMainWindow):
    def __init__(self, token):
        super(SearchScreen, self).__init__()
        self.token = token
        self.mod_name = "search"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/searchwindow.ui"), self)
        self.window().setWindowTitle("Search")

        self.goto_boxes_btn.clicked.connect(self.gotoBoxes)

        self.search_tab_wg.setCurrentIndex(0)
        self.search_tab_wg.currentChanged.connect(self.tabChanged)
        self.export_btn.clicked.connect(self.export_multvial)

        self.mult_vial_search_btn.clicked.connect(self.search_many_vials)
        self.vial_search_eb.textChanged.connect(self.check_vial_search_input)
        self.onevial_checkout_cb.addItems([None,
                                           'a location',
                                           'another location',
                                           'a third location'])
        self.discard_vial_btn.clicked.connect(self.discardVial)
        self.print_label_btn.clicked.connect(self.printLabel)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            if self.search_tab_wg.currentIndex() == 1:
                self.search_many_vials()
                return
            elif self.search_tab_wg.currentIndex() == 2:
                #self._search_batches()
                return
            else: # tab 0, no btn
                return

    def tabChanged(self):
        page_index = self.search_tab_wg.currentIndex()
        if page_index == 0:
            self.vial_search_eb.setFocus()
        elif page_index == 1:
            self.mult_vial_search_eb.setFocus()
        elif page_index == 2:
            self.batch_search_eb.setFocus()

    def gotoBoxes(self):
        from boxesscreen import BoxesScreen
        resize_window(self)
        boxes = BoxesScreen(self.token)
        self.window().addWidget(boxes)
        self.window().setCurrentIndex(self.window().currentIndex() + 1)

    def search_many_vials(self):
        vials = self.mult_vial_search_eb.text()
        print(vials)
        res = dbInterface.getManyVials(self.token, vials)
        self.multvial_data = None
        try:
            self.multvial_data = json.loads(res)
        except:
            print("error")
            print(self.multvial_data)
            self.multvial_data = None
            return
            # clear self.multival_data
        print(self.multvial_data)
        self.multvial_table.setRowCount(len(self.multvial_data))
        self.setMultvialTableData(self.multvial_data)
        

    def setMultvialTableData(self, data):
        for n in range(len(data)): # row n
            print(f'{n}')
            newItem = QTableWidgetItem(f"{data[n]['vialId']}")
            self.multvial_table.setItem(n, 0, newItem)
            newItem = QTableWidgetItem(f"{data[n]['boxDescription']}")
            self.multvial_table.setItem(n, 1, newItem)
            newItem = QTableWidgetItem(f"{data[n]['pos']}")
            self.multvial_table.setItem(n, 2, newItem)
            newItem = QTableWidgetItem(f"{data[n]['path']}")
            newItem.setToolTip(f"{data[n]['path']}")
            self.multvial_table.setItem(n, 3, newItem)
            newItem = QTableWidgetItem(f"{data[n]['batchId']}")
            self.multvial_table.setItem(n, 4, newItem)
            newItem = QTableWidgetItem(f"{data[n]['compoundId']}")
            self.multvial_table.setItem(n, 5, newItem)
            newItem = QTableWidgetItem(f"{data[n]['batchMolWeight']}")
            self.multvial_table.setItem(n, 6, newItem)
            newItem = QTableWidgetItem(f"{data[n]['dilution']}")
            self.multvial_table.setItem(n, 7, newItem)  

    def export_multvial(self):
        mat = [[self.multvial_table.item(row, col).text() for col in range(self.multvial_table.columnCount())] for row in range(self.multvial_table.rowCount())]
        csv = '\n'.join(list(map(lambda x: ', '.join(x), mat)))
        clipboard = QApplication.clipboard()
        clipboard.setText(csv)
        send_msg("Export data", "Data copied to clipboard!")


    def check_vial_search_input(self):
        print("verify input")
        pattern = '^v[0-9]{6}$'
        t = self.vial_search_eb.text()
        if re.match(pattern, t):
            print(f"pattern match: {t}")
            self.searchVial(t)

    def searchVial(self, vialId):
        res = dbInterface.getVialInfo(self.token, vialId)
        try:
            ret = json.loads(res)
        except:
            self.errorlabel.setText(res)
            self.onevial_batch_eb.setText('')
            self.onevial_compound_id_eb.setText('')
            self.onevial_box_loc_eb.setText('')
            self.onevial_coords_eb.setText('')
            self.onevial_checkout_cb.setCurrentText(None)
            self.structure_lab.clear()
            print(res)
            return
        self.errorlabel.setText('')
        print(f'ret: {ret}')
        self.onevial_batch_eb.setText(ret[0]['batch_id'])
        self.onevial_compound_id_eb.setText(ret[0]['compound_id'])
        self.onevial_box_loc_eb.setText(ret[0]['box_id'])
        self.onevial_coords_eb.setText(str(ret[0]['coordinate']))
        self.onevial_checkout_cb.setCurrentText('a location')
        displayMolfile(self, vialId)

    def discardVial(self):
        print(f"discard vial {self.vial_search_eb.text()}")

    def printLabel(self):
        print(f"print label {self.vial_search_eb.text()}")

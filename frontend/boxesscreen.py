import sys, os, logging, re
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem, QAbstractItemView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from cellolib import *

class BoxesScreen(QMainWindow):
    from cellolib import gotoSearch, gotoVials, gotoMicrotubes, gotoPlates
    def __init__(self, token):
        super(BoxesScreen, self).__init__()
        self.token = token
        self.mod_name = "boxes"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/boxeswindow.ui"), self)
        self.window().setWindowTitle("Boxes")

        self.goto_search_btn.clicked.connect(self.gotoSearch)
        self.goto_vials_btn.clicked.connect(self.gotoVials)
        self.goto_microtubes_btn.clicked.connect(self.gotoMicrotubes)
        self.goto_plates_btn.clicked.connect(self.gotoPlates)
        
        self.boxes_tab_wg.setCurrentIndex(0)
        self.boxes_tab_wg.currentChanged.connect(self.tabChanged)

        #locations = [None,]
        #self.add_location_cb.addItems(locations)
        types = [None, "200", "64", "50", 'Matrix',]
        self.add_box_type_cb.addItems(types)
        self.add_box_btn.clicked.connect(self.addBox)
        self.add_box_btn.setEnabled(False)

        types = [None, "Room", "Fridge-Freezer", "Shelf"]
        self.add_location_type_cb.addItems(types)
        self.add_location_btn.clicked.connect(self.addLocation)
        self.add_location_btn.setEnabled(False)

        self.boxes_tree.clear()
        self.init_boxes_tree()
        self.boxes_tree.itemExpanded.connect(self.get_children)
        self.boxes_tree.itemCollapsed.connect(self.take_children)
        self.boxes_tree.currentItemChanged.connect(self.setAddParams)
        self.boxes_tree.currentItemChanged.connect(self.check_addbox_input)
        self.boxes_tree.currentItemChanged.connect(self.check_addlocation_input)
        self.boxes_tree.currentItemChanged.connect(self.check_deletion_params)
        self.boxes_tree.currentItemChanged.connect(self.selectSerialNo)

        self.boxes_tree_reload_btn.clicked.connect(self.reload_tree)

        self.box_search_btn.clicked.connect(self.find_in_box_tree)

        self.add_box_type_cb.currentTextChanged.connect(self.check_addbox_input)
        self.add_description_eb.textChanged.connect(self.check_addbox_input)

        self.add_location_type_cb.currentTextChanged.connect(self.check_addlocation_input)
        self.location_description_eb.textChanged.connect(self.check_addlocation_input)

        self.delete_checkbox.setEnabled(False)
        self.delete_location_btn.setEnabled(False)
        self.delete_checkbox.stateChanged.connect(self.enableDelete)
        self.delete_location_btn.clicked.connect(self.deleteLocation)

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
                if self.box_search_eb.text() != "":
                    self.find_in_box_tree()
                return
            else: # index = 1
                # maybe not?
                return

    def tabChanged(self):
        page_index = self.boxes_tab_wg.currentIndex()
        if page_index == 0:
            #self.boxes_tree.clear()
            #self.init_boxes_tree()
            self.add_description_eb.setFocus()
            self.structure_lab.clear()
        elif page_index == 1:
            self.update_box_eb.setFocus()
            self.box_moldisplay(self.box_table.currentItem())
        elif page_index == 2:
            self.freebox_table.setFocus()
            self.structure_lab.clear()
            self.fetch_free_boxes()


    def locationInput(self, js):
        return [js['NAME'], js['type'], js['LOC_ID']]

    def init_boxes_tree(self):
        # get top level nodes
        r = dbInterface.getLocationChildren(self.token, "root")
        try:
            root_items = json.loads(r)
        except:
            logging.getLogger(self.mod_name).error("bad response for getLocationChildren/root")
            return

        for js in root_items:
            item = QTreeWidgetItem(self.boxes_tree, self.locationInput(js))
            item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)

    def get_children(self, item):
        self.delete_location_error_lab.setText('')
        self.take_children(item)
        loc = item.text(2)
        r = dbInterface.getLocationChildren(self.token, loc)
        children = []
        try:
            children = json.loads(r)
        except:
            logging.getLogger(self.mod_name).error(f"bad response for getLocationChildren/{loc}")
            return
        for child in children:
            childItem = QTreeWidgetItem(item, self.locationInput(child))
            if child['has_children'] == -1:
                childItem.setChildIndicatorPolicy(QTreeWidgetItem.DontShowIndicator)
            else:
                childItem.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
        return len(children)
        

    def take_children(self, item):
        children = item.takeChildren()
        l = [f'({child.text(0)}:{child.text(2)})' for child in children]
        #if len(l) > 0:
            #print("took " + ', '.join(l))

    def find_in_box_tree(self):
        path = None
        s = self.box_search_eb.text()
        if s != "":
            try:
                res = dbInterface.getLocationPath(self.token, s)
                path = json.loads(res)
            except:
                logging.getLogger(self.mod_name).error(f"getLocationPath returned {res}")
                return
            if len(path) > 0:
                self.seek_path(path[0]['path'])

    def seek_path(self, path_s):
        path_l = path_s.split('/')
        for p in path_l:
            items = self.boxes_tree.findItems(p, Qt.MatchRecursive)
            self.boxes_tree.setCurrentItem(items[0])
            self.boxes_tree.expandItem(items[0])   

    def selectSerialNo(self, item):
        try:
            if self.boxes_tree.currentColumn() == 2:
                return
            else:
                self.boxes_tree.setCurrentItem(item, 2)
        except:
            return

    def reload_tree(self):
        self.boxes_tree.clear()
        self.init_boxes_tree()
        if self.box_search_eb.text() != "":
            self.find_in_box_tree()


    def setAddParams(self, item):
        if (item is not None):
            self.add_location_lab.setText(item.text(0))
            self.add_storage_type_lab.setText(item.text(1))

            self.location_location_lab.setText(item.text(0))
            self.location_storage_type_lab.setText(item.text(1))

            self.delete_location_lab.setText(item.text(0))
            self.delete_storage_type_lab.setText(item.text(1))

            self.add_location_barcode = item.text(2)
        else:
            self.add_location_lab.setText("")
            self.add_storage_type_lab.setText("")

            self.location_location_lab.setText("")
            self.location_storage_type_lab.setText("")

            self.delete_location_lab.setText("")
            self.delete_storage_type_lab.setText("")

            self.add_location_barcode = None

    def resetInput(self):
        self.add_description_eb.setText('')
        self.add_box_type_cb.setCurrentText(None)
        self.add_box_btn.setEnabled(False)

        self.add_location_type_cb.setCurrentText(None)
        self.location_description_eb.setText('')

    def addBox(self):
        sBoxName = self.add_description_eb.text()
        sBoxSize = self.add_box_type_cb.currentText()
        sParent = self.add_location_barcode
        r = dbInterface.addBox(self.token, sParent, sBoxName, sBoxSize)
        if r:
            self.resetInput()
            self.boxes_tree.collapseItem(self.boxes_tree.currentItem())
            self.boxes_tree.expandItem(self.boxes_tree.currentItem())
        else:
            #TODO send error message
            logging.getLogger(self.mod_name).error(f"addBox failed with [{sBoxName}, {sBoxSize}, {sParent}]")

    def check_addbox_input(self):
        if (self.add_location_lab.text() != "") and \
            (self.add_box_type_cb.currentText() != "") and \
            (self.add_description_eb.text() != "") and \
            (self.boxes_tree.currentItem().childIndicatorPolicy() != QTreeWidgetItem.DontShowIndicator):
            self.add_box_btn.setEnabled(True)
        else:
            self.add_box_btn.setEnabled(False)

    def addLocation(self):
        sLocationName = self.location_description_eb.text()
        sLocationType = self.add_location_type_cb.currentText()
        sParent = self.add_location_barcode
        r = dbInterface.addLocation(self.token, sParent, sLocationName, sLocationType)
        if r:
            self.resetInput()
            self.boxes_tree.collapseItem(self.boxes_tree.currentItem())
            self.boxes_tree.expandItem(self.boxes_tree.currentItem())
        else:
            #TODO send error message
            logging.getLogger(self.mod_name).error(f"addLocation failed with [{sLocationName}, {sLocationType}, {sParent}]")

    def check_addlocation_input(self):
        if (self.location_location_lab.text() != "") and \
            (self.add_location_type_cb.currentText() != "") and \
            (self.location_description_eb.text() != "") and \
            (self.boxes_tree.currentItem().childIndicatorPolicy() != QTreeWidgetItem.DontShowIndicator):
            self.add_location_btn.setEnabled(True)
        else:
            self.add_location_btn.setEnabled(False)

    def deleteLocation(self):
        target = f"{self.delete_location_lab.text()}/{self.add_location_barcode}"
        #target_barcode = self.add_location_barcode 
        logging.getLogger(self.mod_name).info(f"delete {target}!")
        
        #delete request
        r, ret = dbInterface.deleteLocation(self.token, self.add_location_barcode)
        if ret is False:
            #TODO send error message
            self.delete_location_error_lab.setText(r.content.decode())
            logging.getLogger(self.mod_name).error(f"error removing {target}: {r.content.decode()}")
            self.resetInput()
            return
        #reload parents children
        #select parent
        self.boxes_tree.setCurrentItem(self.boxes_tree.currentItem().parent())
        self.boxes_tree.collapseItem(self.boxes_tree.currentItem())
        self.boxes_tree.expandItem(self.boxes_tree.currentItem())
        self.resetInput()

    def check_deletion_params(self):
        if self.boxes_tree.currentItem() is not None:
            #self.take_children(self.boxes_tree.currentItem())
            nr_o_children = self.get_children(self.boxes_tree.currentItem())
            if (nr_o_children == 0) or \
               (self.boxes_tree.currentItem().childIndicatorPolicy() == QTreeWidgetItem.DontShowIndicator):
                self.delete_checkbox.setEnabled(True)
                self.delete_checkbox.setChecked(False)
                self.delete_location_btn.setEnabled(False)
                return
        self.delete_checkbox.setEnabled(False)
        self.delete_checkbox.setChecked(False)
        self.delete_location_btn.setEnabled(False)

    def enableDelete(self, state):
        if state == 2:
            self.delete_location_btn.setEnabled(True)
        else:
            self.delete_location_btn.setEnabled(False)


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
        r, c = getNextFreeRow(self.box_table, row, 0)
        if r == -1:
            self.box_table.setCurrentCell(0, 0)
            self.box_table.scrollToItem(self.box_table.item(0, 0), QAbstractItemView.PositionAtCenter)
        else:
            self.box_table.setCurrentCell(r, 0)
            self.box_table.editItem(self.box_table.item(r, col))
            self.box_table.scrollToItem(self.box_table.item(r, col), QAbstractItemView.PositionAtCenter)
            
            
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
        try:
            for n in range(len(data)):
                newItem = QCustomTableWidgetItem(f"{data[n]['free_positions']}")
                newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
                self.freebox_table.setItem(n, 0, newItem)
                newItem = QTableWidgetItem(f"{data[n]['name']}")
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

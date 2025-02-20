from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QFileDialog, QListWidget, QDialog, QMessageBox
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QColor
from assets.listEdit import Ui_ListEdit
from cellolib import *
import re

class MyListClass(QDialog):  # Inherit from QDialog
    def __init__(self, saTypes, parent=None):  # Add parent argument
        super().__init__(parent)  # Initialize parent
        self.parent = parent
        self.ui = Ui_ListEdit()
        self.ui.setupUi(self)
        self.setModal(True)
        self.setWindowTitle("List Edit")
        for sType in saTypes:
            self.ui.listType_cb.addItem(sType)
        self.listNameOk = False
        self.ui.saveList_btn.clicked.connect(self.saveList)
        self.ui.saveList_btn.setEnabled(False)
        self.ui.insertList_btn.clicked.connect(self.insertList)
        self.ui.list_tab.installEventFilter(self)  # Install event filter

        self.ui.listName_eb.textChanged.connect(self.nameChanged)

        # listName_eb list name edit box 
        # list_tab   table for batches

    def eventFilter(self, obj, event):
        if obj == self.ui.list_tab and event.type() == QEvent.KeyPress:
            keyEvent = event
            if keyEvent.modifiers() == Qt.ControlModifier and keyEvent.key() == Qt.Key_C:  # Ctrl+C
                self.copy_selected_cells()
                return True  # Event handled
            elif keyEvent.modifiers() == Qt.ControlModifier and keyEvent.key() == Qt.Key_V:  # Ctrl+V
                self.pasteList()
                return True  # Event handled
            elif keyEvent.modifiers() == Qt.ControlModifier and keyEvent.key() == Qt.Key_X:  # Ctrl+X
                self.delete_selected_rows()
                return True
        return super().eventFilter(obj, event)

    def nameChanged(self):
        lIsNameUnique = False
        ebName = self.ui.listName_eb.text()
        if len(ebName) > 0:
            lIsNameUnique = dbInterface.checkListName(self.parent.token, ebName)
        else:
            self.listNameOk = False
            self.ui.saveList_btn.setEnabled(False)
            return
        
        if lIsNameUnique:
            self.listNameOk = True
        
    
    def all_status_ok(self):
        """Checks if all values in the second column of the table are 'Ok'.

            Returns:
            True if all values are 'Ok', False otherwise.
        """
        row_count = self.ui.list_tab.rowCount()

        if row_count == 0:  # Handle empty table case.
            self.ui.saveList_btn.setEnabled(False)
            return False # Or True, depending on your application logic

        for row in range(row_count):
            item = self.ui.list_tab.item(row, 1)  # Column 1 is the second column
            if item is None or item.text() != 'Ok': # Check for None or not "Ok"
                self.ui.saveList_btn.setEnabled(False)
                return False  # Found a value that is not 'Ok' or cell is empty
        if self.listNameOk == True:
            self.ui.saveList_btn.setEnabled(True)
        return True  # All values are 'Ok'


    def copy_selected_cells(self):
        selected_ranges = self.ui.list_tab.selectedRanges()

        if not selected_ranges:
            QMessageBox.information(self, "Information", "No cells selected.")
            return
        copied_text = ""

        # Sort ranges to ensure correct order in copied text.
        selected_ranges.sort(key=lambda r: (r.topRow(), r.leftColumn()))

        for selection_range in selected_ranges:  # Iterate through the selection ranges
            for row in range(selection_range.topRow(), selection_range.bottomRow() + 1):
                for col in range(selection_range.leftColumn(), selection_range.rightColumn() + 1):
                    item = self.ui.list_tab.item(row, col)
                    if item is not None:
                        copied_text += item.text()
                    if col != selection_range.rightColumn():
                        copied_text += "\t"
                copied_text += "\n"

        if copied_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(copied_text)
            print("Selected cells copied to clipboard.")
        else:
            QMessageBox.information(self, "Information", "No cell with text was selected.")

    def delete_selected_rows(self):
        selected_ranges = self.ui.list_tab.selectedRanges()

        if not selected_ranges:
            QMessageBox.information(self, "Information", "No rows selected.")
            return

        # Get the selected rows (unique and sorted)
        selected_rows = set()
        for selection_range in selected_ranges:
            for row in range(selection_range.topRow(), selection_range.bottomRow() + 1):
                selected_rows.add(row)
        
        sorted_rows = sorted(list(selected_rows), reverse=True) # Sort in reverse order to avoid index issues

        # Delete the rows (in reverse order to avoid index issues)
        for row in sorted_rows:
            self.ui.list_tab.removeRow(row)

        values = self.get_first_column_values()
        #self.validateValues(values)
        self.all_status_ok()

    def get_first_column_values(self):
        """Returns a list of all values from the first column of the table."""
        row_count = self.ui.list_tab.rowCount()
        first_column_values = []

        for row in range(row_count):
            item = self.ui.list_tab.item(row, 0)  # Column 0 is the first column
            if item is not None:  # Check if the cell has an item
                first_column_values.append(item.text())
            else:
                first_column_values.append("")  # Or append None, or handle empty cells as you prefer
        return first_column_values


    def validateValues(self, valueList):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        accumulated_rows = []
        iAccumulator_count = 0
        iRowsBatch = 10
        self.popup = PopUpProgress(f'Validating list...')
        self.popup.show()
        iNrOfRows = len(valueList)
        iTick = 0
        iCount = 0
        rProgressSteps = (iRowsBatch/iNrOfRows)*100
        sAccuBatches = ''
        listType = self.ui.listType_cb.currentText()
        
        saValidatedData = []
        for value in valueList:
            iCount += 1
            sAccuBatches = sAccuBatches + ' ' + value
            if iCount == iRowsBatch:
                res = dbInterface.validateBatch(self.parent.token, sAccuBatches, listType)
                for row in res:
                    if row[1] != 'Ok':
                        saValidatedData = [row] + saValidatedData
                    else:
                        saValidatedData.append(row)
                iCount = 0
                sAccuBatches = ''
                iTick += rProgressSteps
                self.popup.obj.proc_counter(int(iTick))
                QApplication.processEvents()
        if sAccuBatches != '':
            res = dbInterface.validateBatch(self.parent.token, sAccuBatches, listType)
            for row in res:
                if row[1] != 'Ok':
                    saValidatedData = [row] + saValidatedData
                else:
                    saValidatedData.append(row)
                    
        self.popup.obj.proc_counter(100)
        self.popup.close()
        QApplication.restoreOverrideCursor()
        return saValidatedData

    def insertList(self):
        print('Inserting')
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        text = text.replace(",", " ")

        
    def pasteList(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        text = text.replace(",", " ")
        values = []
        if text:
            try:
                tokens = text.splitlines()  # First try splitting by lines
                #if not tokens: # If there were no lines, split by spaces
                tokens = text.split()

                # 2. Populate the first column
                row_count = len(tokens)
                self.ui.list_tab.setRowCount(0) # Clear existing data
                self.ui.list_tab.setRowCount(row_count)
                for row_index, token in enumerate(tokens):
                    token = "".join(c for c in token if not c.isspace())
                    token = re.sub(r'\W+', '', token)
                    values.append(token)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error pasting data: {e}")
                print(f"Error pasting data: {e}")
        else:
            QMessageBox.information(self, "Information", "Clipboard is empty.")
            print("Clipboard is empty.")

        #values = self.get_first_column_values()
        validatedValues = self.validateValues(values)
        
        for row_index, row in enumerate(validatedValues):
            status = QTableWidgetItem(row[1])
            item = QTableWidgetItem(row[0])
            self.ui.list_tab.setItem(row_index, 0, item)  # Column 0 is the first column
            self.ui.list_tab.setItem(row_index, 1, status)  # Column 1 is the status

            if row[1] != 'Ok':  # Check if status is NOT 'Ok'
                for col in range(self.ui.list_tab.columnCount()):  # Color all cells in the row
                    item = self.ui.list_tab.item(row_index, col)
                    if item is not None:  # Check if the cell has an item
                        item.setForeground(QColor("red"))  # Set the foreground (font) color to red
        self.all_status_ok()


    def saveList(self):
        ebName = self.ui.listName_eb.text()
        listType = self.ui.listType_cb.currentText()
        dbInterface.createList(self.parent.token, ebName, listType)

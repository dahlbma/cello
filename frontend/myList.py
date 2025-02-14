from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QFileDialog, QListWidget, QDialog, QMessageBox
from PyQt5.QtCore import Qt, QEvent
from assets.listEdit import Ui_ListEdit

class MyListClass(QDialog):  # Inherit from QDialog
    def __init__(self, parent=None):  # Add parent argument
        super().__init__(parent)  # Initialize parent
        self.parent = parent
        self.ui = Ui_ListEdit()
        self.ui.setupUi(self)
        self.setModal(True)
        self.setWindowTitle("List Edit")
        self.ui.listType_cb.addItem("Batch Id")
        self.ui.saveList_btn.clicked.connect(self.saveList)
        self.ui.pasteList_btn.clicked.connect(self.pasteList)
        self.ui.list_tab.installEventFilter(self)  # Install event filter

        # listName_eb list anme edit box 
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


    def pasteList(self):  # Example method to get data from the dialog
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        text = text.replace(",", " ")
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
                    status = QTableWidgetItem("Unchecked")
                    item = QTableWidgetItem(token)
                    self.ui.list_tab.setItem(row_index, 0, item)  # Column 0 is the first column
                    self.ui.list_tab.setItem(row_index, 1, status)  # Column 1 is the status

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error pasting data: {e}") # Show a message box
                print(f"Error pasting data: {e}")
        else:
            QMessageBox.information(self, "Information", "Clipboard is empty.") # Show a message box
            print("Clipboard is empty.")


    def saveList(self):
        pass


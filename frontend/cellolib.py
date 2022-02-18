import imp
import sys, requests, json, os, subprocess, platform, shutil, datetime, traceback, logging, dbInterface
from PyQt5.QtGui import QImage, QPixmap
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMessageBox, QTableWidget, QTableWidgetItem

class QCustomTableWidgetItem (QTableWidgetItem):
    def __init__ (self, value):
        super(QCustomTableWidgetItem, self).__init__(value)

    def __lt__ (self, other):
        if (isinstance(other, QCustomTableWidgetItem)):
            selfDataValue  = float(self.text())
            otherDataValue = float(other.text())
            return selfDataValue < otherDataValue
        else:
            return QTableWidgetItem.__lt__(self, other)


def gotoSearch(self):
    resize_window(self)
    self.window().setCurrentIndex(1)
    self.window().widget(1).search_tab_wg.setCurrentIndex(0)
    self.window().widget(1).vial_search_eb.setFocus()
    return

def gotoVials(self):
    resize_window(self)
    self.window().setCurrentIndex(2)
    self.window().widget(2).vials_tab_wg.setCurrentIndex(0)
    self.window().widget(2).edit_vial_id_eb.setFocus()
    return

def gotoBoxes(self):
    resize_window(self)
    self.window().setCurrentIndex(3)
    self.window().widget(3).boxes_tab_wg.setCurrentIndex(0)
    self.window().widget(3).add_description_eb.setFocus()
    return

def gotoLocations(self):
    return

def gotoMicrotubes(self):
    resize_window(self)
    self.window().setCurrentIndex(5)
    self.window().widget(5).microtubes_tab_wg.setCurrentIndex(0)
    self.window().widget(5).tubes_batch_eb.setFocus()
    return

def send_msg(title, text, icon=QMessageBox.Information, e=None):
    msg = QMessageBox()
    msg.setWindowTitle(title)
    msg.setIcon(icon)
    msg.setText(text)
    clipboard = QApplication.clipboard()
    if e is not None:
        # add clipboard btn
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Save)
        buttonS = msg.button(QMessageBox.Save)
        buttonS.setText('Save to clipboard')
    msg.exec_()
    if e is not None:
        if msg.clickedButton() == buttonS:
            # copy to clipboard if clipboard button was clicked
            clipboard.setText(text)
            cb_msg = QMessageBox()
            cb_msg.setText(clipboard.text()+" \n\ncopied to clipboard!")
            cb_msg.exec_()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def resize_window(self, height=800, width=1200):
    desktop = QApplication.desktop()

    windowHeight = int(round(0.9 * desktop.screenGeometry().height(), -1))
    if windowHeight > height:
        windowHeight = height

    windowWidth = int(round((width/height) * windowHeight, -1))

    self.window().resize(windowWidth, windowHeight)

def displayMolfile(self, vial):
    dbInterface.createMolImage(self.token, vial.lower())
    image = QImage()
    self.structure_lab.setScaledContents(True)
    image.loadFromData(dbInterface.getMolImage(vial.lower()))
    self.structure_lab.setPixmap(QPixmap(image))

def export_table(table):
        mat = [[table.item(row, col).text() for col in range(table.columnCount())] for row in range(table.rowCount())]
        csv = '\n'.join(list(map(lambda x: ', '.join(x), mat)))
        clipboard = QApplication.clipboard()
        clipboard.setText(csv)
        send_msg("Export data", "Data copied to clipboard!")

def getNextFreeRow(table, row):
    for r in range(row + 1, table.rowCount()):
        if table.item(r, 0).text() == "":
            return r
    return -1


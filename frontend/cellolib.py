import imp
import sys, requests, json, os, subprocess, platform, shutil, datetime, traceback, logging, dbInterface
from PyQt5.QtGui import QImage, QPixmap
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMessageBox, QTableWidget

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
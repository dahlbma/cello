import imp
import sys, requests, json, os, subprocess, platform, shutil, datetime, traceback, logging, dbInterface
from unittest import result
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
    #self.window().widget(1).search_tab_wg.setCurrentIndex(0)
    self.window().widget(1).vial_search_eb.setFocus()
    return

def gotoVials(self):
    resize_window(self)
    self.window().setCurrentIndex(2)
    #self.window().widget(2).vials_tab_wg.setCurrentIndex(0)
    self.window().widget(2).edit_vial_id_eb.setFocus()
    return

def gotoBoxes(self):
    resize_window(self)
    self.window().setCurrentIndex(3)
    #self.window().widget(3).boxes_tab_wg.setCurrentIndex(0)
    self.window().widget(3).add_description_eb.setFocus()
    return

def gotoMicrotubes(self):
    resize_window(self)
    self.window().setCurrentIndex(4)
    #self.window().widget(4).microtubes_tab_wg.setCurrentIndex(0)
    self.window().widget(4).tubes_batch_eb.setFocus()
    return

def gotoPlates(self):
    resize_window(self)
    self.window().setCurrentIndex(5)
    #self.window().widget(5).plates_tab_wg.setCurrentIndex(0)
    self.window().widget(5).new_n_plates_sb.setFocus()
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

def displayMolfile(self, sId):
    dbInterface.createMolImage(self.token, sId.upper())
    image = QImage()
    self.structure_lab.setScaledContents(True)
    image.loadFromData(dbInterface.getMolImage(sId.upper()))
    self.structure_lab.setPixmap(QPixmap(image))

def export_table(table):
        mat = [[table.item(row, col).text() for col in range(table.columnCount())] for row in range(table.rowCount())]
        csv = '\n'.join(list(map(lambda x: ', '.join(x), mat)))
        clipboard = QApplication.clipboard()
        clipboard.setText(csv)
        send_msg("Export data", "Data copied to clipboard!")

def getNextFreeRow(table, row, col, entireRowFree=False, fromSame=False):
    start = 1
    if fromSame:
        start = 0
    for r in range(row + start, table.rowCount()):
        item = table.item(r, col)
        if entireRowFree:
            itemList = []
            for c in range(table.columnCount()):
                itemList.append(table.item(r, c))
                if all((it is None) or (it.text() == "") for it in itemList):
                    return r, 0
        else:
            if (item is None) or (item.text() == ""):
                return r, col
    return -1, -1

def plate_to_html(data, size1, resultdata, size2):
    html = chart_html(data, size1)
    optional = ""
    if size2 != None:
        optional = "<span class=\"normal\"></br></br>to</br></br></br></span>" \
                   + chart_html(resultdata, size2)
    return chart_lambda()(html, optional)

def chart_html(data, size):
    scale = {'96':1, '384':2, '1536':4}[str(size)]
    rows = 8*scale
    cols = 12*scale

    chart = [["blue" for _ in range(cols)] for _ in range(rows)]

    if data != None:
        for well in data:
            info = well['well']
            row = int(ord(info[0]) - ord('A'))
            col = int(info[1:]) - 1
            chart[row][col] = "red"

    span = lambda x: f"<span class=\"{x}\"></span>"
    html = ""
    for i in range(rows):
        for j in range(cols):
            html += span(chart[i][j])
            if j == 11:
                html += "<span class=\"normal\"> </span>" #"&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"
        if i == 7:
            html += "</br>"
        html += "</br>"
    return html

def chart_lambda():
    return lambda x, y: f"""<!DOCTYPE html><html><head><style>
.red {"{"}
  height: 10px;
  width: 10px;
  background-color: red;
  border-radius: 50%;
  display: inline-block;
{"}"}
.blue {"{"}
  height: 6px;
  width: 6px;
  border: 2px solid blue;
  border-radius: 50%;
  display: inline-block;
{"}"}
.normal {"{"}
  letter-spacing: normal;
{"}"}
</style></head><body><div style="text-align:center; line-height:10px; letter-spacing: -4px;">
{x}
{y}
</div></body></html>"""
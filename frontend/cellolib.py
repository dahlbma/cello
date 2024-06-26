import sys, requests, json, os, subprocess, platform, shutil, datetime, traceback, logging, dbInterface, re
from unittest import result
from PyQt5.QtGui import QImage, QPixmap
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMessageBox, QTableWidget, QTableWidgetItem, QWidget
from PyQt5.QtWidgets import QProgressBar, QVBoxLayout
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot

class Worker(QObject):
    finished = pyqtSignal()
    intReady = pyqtSignal(int)

    @pyqtSlot()
    def proc_counter(self, i = 1):
        if i < 100:
            self.intReady.emit(i)
        else:
            self.finished.emit()

#progressbar
class PopUpProgress(QWidget):

    def __init__(self, sHeader = ""):
        super().__init__()
        self.pbar = QProgressBar(self)
        self.pbar.setGeometry(30, 40, 500, 75)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.pbar)
        self.setLayout(self.layout)
        self.setGeometry(300, 300, 550, 100)
        self.setWindowTitle(sHeader)
        self.pbar.show()

        self.thread = QtCore.QThread()
        self.obj = Worker()
        self.obj.intReady.connect(self.on_count_changed)
        self.obj.moveToThread(self.thread)
        self.obj.finished.connect(self.thread.quit)
        self.thread.started.connect(self.obj.proc_counter)
        self.thread.start()

    def on_count_changed(self, value):
        self.pbar.setValue(value)

#sortable table items
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

# navigation between top-level sections
def gotoSearch(self):
    resize_window(self)
    self.window().setCurrentIndex(1)
    self.window().widget(1).vial_search_eb.setFocus()
    return

def gotoVials(self):
    resize_window(self)
    self.window().setCurrentIndex(2)
    self.window().widget(2).edit_vial_id_eb.setFocus()
    return

def gotoBoxes(self):
    resize_window(self)
    self.window().setCurrentIndex(3)
    self.window().widget(3).add_description_eb.setFocus()
    return

def gotoMicrotubes(self):
    resize_window(self)
    self.window().setCurrentIndex(4)
    self.window().widget(4).tubes_batch_eb.setFocus()
    return

def gotoPlates(self):
    resize_window(self)
    self.window().setCurrentIndex(5)
    self.window().widget(5).new_n_plates_sb.setFocus()
    return

#custom notification toolbox
def send_msg(title, text, icon=QMessageBox.Information, e=None):
    msg = QMessageBox()
    msg.setWindowTitle(title)
    msg.setIcon(icon)
    msg.setText(text)
    clipboard = QApplication.clipboard()
    if e is not None:
        #add clipboard btn
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Save)
        buttonS = msg.button(QMessageBox.Save)
        buttonS.setText('Save to clipboard')
    msg.exec_()
    if e is not None:
        if msg.clickedButton() == buttonS:
            #copy to clipboard if clipboard button was clicked
            clipboard.setText(text)
            cb_msg = QMessageBox()
            cb_msg.setText(clipboard.text()+" \n\ncopied to clipboard!")
            cb_msg.exec_()

#gets asset path from app execution path/pyinstaller package
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
        csv = '\n'.join(list(map(lambda x: ','.join(x), mat)))
        clipboard = QApplication.clipboard()
        clipboard.setText(csv)
        send_msg("Export data", "Data copied to clipboard!")

#better UX, steps between rows in input table, for scanning multiple barcodes
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

# plate_to_html 1 / 4, parses plate/rack data and returns html
def plate_to_html(data, size1, resultdata, size2):
    html = chart_html(data, size1, "_s")
    optional = ""
    #set default blob sizes for printing only one plate
    blob_size1, blob_size2 = 8, 8
    if size2 != None:
        optional = "<span class=\"normal\"></br></br>to</br></br></br></span>" \
                   + chart_html(resultdata, size2, "_t")
    try:
        blob_size1 = {'96':8, '384':8, '1536':2}[str(size1)]
    except:
        return ""
    if size2 != None:
        blob_size2 = {'96':8, '384':8, '1536':2}[str(size2)]
    outtext = chart2(blob_size1, blob_size2)(html, optional)
    return outtext

# plate_to_html 2 / 4, helper function, parses plate/rack data to 2d string array
def chart_html(data, size, pf='_s'):
    try:
        scale = {'96':1, '384':2, '1536':4}[str(size)]
        rows = 8*scale
        cols = 12*scale
    except:
        return ""

    chart = [["blue" + pf for _ in range(cols)] for _ in range(rows)]

    if data != None:
        for well in data:
            try:
                info = well['well']
            except:
                info = well['position']
            if scale < 4:
                row = int(ord(info[0]) - ord('A'))
                col = int(info[1:]) - 1
            else:
                parts = re.split(r'(\d+)', info)
                row_c = parts[0]
                if len(row_c) == 1:
                    row = int(ord(row_c[0]) - ord('A'))
                elif len(row_c) == 2:
                    row = int(ord(row_c[1]) - ord('A')) + 26

                col = int(parts[1]) - 1

            try:
                if well['compound_id'].startswith('CTRL'):
                    chart[row][col] = "green" + pf
                elif well['compound_id'] == 'DMSO':
                    chart[row][col] = "black" + pf
                else:
                    chart[row][col] = "red" + pf
            except:
                # We end up here when we are scanning microtube racks
                chart[row][col] = "red" + pf

    span = lambda x: f"<span class=\"{x}\"></span>"
    html = ""
    for i in range(rows):
        for j in range(cols):
            html += span(chart[i][j])
            if scale > 1 and j == ((cols / 2) - 1):
                html += "<span class=\"normal\"> </span>"
        if scale > 1 and i == ((rows / 2) - 1):
            html += "</br>"
        html += "</br>"
    return html

# plate_to_html 3 / 4, deprecated version, use chart2 instead
def chart_lambda(blob_size = 8):

    return lambda x, y, size: f"""<!DOCTYPE html><html><head><style>
    .red {"{"}
    height: {blob_size + 2}px;
    width: {blob_size + 2}px;
    background-color: red;
    border-radius: 50%;
    display: inline-block;
    {"}"}
    .green {"{"}
    height: {blob_size + 2}px;
    width: {blob_size + 2}px;
    background-color: green;
    border-radius: 50%;
    display: inline-block;
    {"}"}
    .black {"{"}
    height: {blob_size + 2}px;
    width: {blob_size + 2}px;
    background-color: black;
    border-radius: 50%;
    display: inline-block;
    {"}"}
    .blue {"{"}
    height: {blob_size - 2}px;
    width: {blob_size - 2}px;
    border: 2px solid blue;
    border-radius: 50%;
    display: inline-block;
    {"}"}
    .normal {"{"}
    letter-spacing: normal;
    {"}"}
    </style></head><body><div style="text-align:center; line-height:{blob_size + 2}px; letter-spacing: -4px;">
    {x}
    {y}
    </div></body></html>"""

# plate_to_html 4 / 4, helper function, parses formatted string array to html output
def chart2(blob_size1 = 8, blob_size2 = 8):
    return lambda x, y: f"""<!DOCTYPE html><html><head><style>
    .red_s {"{"}
    height: {blob_size1 + 2}px;
    width: {blob_size1 + 2}px;
    background-color: red;
    border-radius: 50%;
    display: inline-block;
    {"}"}
    .red_t {"{"}
    height: {blob_size2 + 2}px;
    width: {blob_size2 + 2}px;
    background-color: red;
    border-radius: 50%;
    display: inline-block;
    {"}"}
    .green_s {"{"}
    height: {blob_size1 + 2}px;
    width: {blob_size1 + 2}px;
    background-color: green;
    border-radius: 50%;
    display: inline-block;
    {"}"}
    .green_t {"{"}
    height: {blob_size2 + 2}px;
    width: {blob_size2 + 2}px;
    background-color: green;
    border-radius: 50%;
    display: inline-block;
    {"}"}
    .black_s {"{"}
    height: {blob_size1 + 2}px;
    width: {blob_size1 + 2}px;
    background-color: black;
    border-radius: 50%;
    display: inline-block;
    {"}"}
    .black_t {"{"}
    height: {blob_size2 + 2}px;
    width: {blob_size2 + 2}px;
    background-color: black;
    border-radius: 50%;
    display: inline-block;
    {"}"}
    .blue_s {"{"}
    height: {blob_size1 - 2}px;
    width: {blob_size1 - 2}px;
    border: 2px solid blue;
    border-radius: 50%;
    display: inline-block;
    {"}"}
    .blue_t {"{"}
    height: {blob_size2 - 2}px;
    width: {blob_size2 - 2}px;
    border: 2px solid blue;
    border-radius: 50%;
    display: inline-block;
    {"}"}
    .normal {"{"}
    letter-spacing: normal;
    {"}"}
    </style></head><body>
    <div style="text-align:center; line-height:{blob_size1 + 2}px; letter-spacing: -4px;">
    {x}
    </div>
    <div style="text-align:center; line-height:{blob_size2 + 2}px; letter-spacing: -4px;">
    {y}
    </div>
    </body></html>"""

# transforms source plates indices to larger merge target 
def disp_tran(quad, data, size):
        mult = 1 if size == 96 else 2 # no need to display anything larger than 4*384 / 1536
        shiftAlpha = 0
        shiftNum = 0
        if quad == 1:
            return data
        elif quad == 2:
            shiftNum = 12 * mult
        elif quad == 3:
            shiftAlpha = 8 * mult
        elif quad == 4:
            shiftAlpha = 8 * mult
            shiftNum = 12 * mult
        ret = []
        wellColName = 'well'
        try:
            if data[0]['well'] == data[0]['well']:
                wellColName = 'well'
        except:
            wellColName = 'position'
        for well in data:
            new_well = well.copy()
            info = new_well[wellColName]
            row = chr(ord(info[0]) + shiftAlpha)
            try:
                col = int(info[1:]) + shiftNum
            except:
                print(info)
            new_well[wellColName] = f"{row}{col}"
            ret.append(new_well)
        return ret

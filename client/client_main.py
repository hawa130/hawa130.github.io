import sys
import requests
import client_ui
from os import remove
from math import ceil
from json import loads
from time import sleep
from html import unescape
from pyperclip import copy, paste
from datetime import datetime, timedelta
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem

requrl = 'https://abnyvjny.api.lncldglobal.com/1.1/classes/content'
headers = {
    'Content-Type':'application/json',
    'X-LC-Id':'ABnYvjnyRufm05kdQu2SzSFj-MdYXbMMI',
    'X-LC-Key':'PhiYpUWiyAgVwKJIizK8tD8u'
}
diction = ['content', 'author', 'createdAt']

class sendThread(QThread):  #文本发布线程
    trigger = pyqtSignal(int)
    def __init__(self, arg1, arg2):
        super(sendThread, self).__init__()
        self.arg1 = arg1
        self.arg2 = arg2

    def run(self):
        status = Communicate.post(Communicate, self.arg1, self.arg2)
        self.trigger.emit(status)

class tableThread(QThread): #列表获取线程
    trigger = pyqtSignal(dict)
    def __init__(self, arg1, arg2):
        super(tableThread, self).__init__()
        self.arg1 = arg1
        self.arg2 = arg2

    def run(self):
        result = Communicate.getData(self.arg1, self.arg2)
        self.trigger.emit(result)

class ClipThread(QThread):  #剪贴板监听线程
    trigger = pyqtSignal(str)
    def __init__(self):
        super(ClipThread, self).__init__()

    def run(self):
        lateString = paste()
        while MainWindow.checkBox_3.isChecked():
            sleep(0.1)
            string = paste()
            if string == '':
                continue
            if string != lateString != '':
                lateString = string
                self.trigger.emit(lateString)

class Communicate(object):  #服务器端交互
    def __init__(self, arg):
        super(Communicate, self).__init__()
        self.arg = arg

    def toHTML(string):
        string = string.replace('&', '&amp;')
        string = string.replace('>', '&gt;')
        string = string.replace('<', '&lt;')
        string = string.replace('"','&quot;')
        string = string.replace("'",'&#39;')
        string = string.replace(' ','&nbsp;')
        string = string.replace('\n','<br>')
        string = string.replace('\r','<br>')
        return string

    def post(self, content, poster): #发布内容
        data = {
            'content':self.toHTML(content),
            'author':poster,
        }
        req = requests.post(requrl, json = data, headers = headers)
        return req.status_code

    def getData(skip, num): #获取 (skip, skip+num] 的数据
        get = requests.get('%s?order=-createdAt&limit=%d&skip=%d&count=1' % (requrl, num, skip), headers = headers)
        get.encoding = 'utf-8'
        result = loads(get.text)
        return result

    def convertFromUTC(utcTime):
        utcFORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
        utc = datetime.strptime(utcTime, utcFORMAT)
        localTime = utc + timedelta(hours = 8)
        return localTime

class Window(client_ui.Ui_MainWindow, QMainWindow):
    lineNum = 10    #每页行数
    conNum = 0      #项目总数
    skip = 0        #获取项目时跳过的项目数
    maxPage = 1     #最大页码
    savedName = ''  #保存的名称
    def __init__(self):
        super(Window, self).__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.push)
        self.checkBox_3.stateChanged.connect(self.toggleMonitor)
        self.textEdit.textChanged.connect(self.charCount)
        self.textEdit.setFocus()
        self.readSaved()
        self.lineEdit.setText(self.savedName)
        self.tableWidget.setColumnWidth(0, 340)
        self.tableWidget.setColumnWidth(1, 70)
        self.tableWidget.setColumnWidth(2, 110)
        self.tableWidget.cellDoubleClicked.connect(self.copyToClip)
        self.updateTable()
        self.refreshButton.clicked.connect(self.updateTable)
        self.comboBox.editTextChanged.connect(self.updateNum)
        self.Home.clicked.connect(self.setMinimum)
        self.End.clicked.connect(self.setMaximum)
        self.spinBox.valueChanged.connect(self.updateListNum)

    def readSaved(self): #读取记住的名称
        try:
            saved = open('savedName')
        except FileNotFoundError:
            pass
        else:
            self.savedName = saved.readline().replace('\n', '')
            self.checkBox.setChecked(True)

    def saveName(self): #记住名称
        saved = open('savedName', 'w')
        print(self.author, file = saved)
        saved.close()

    def push(self):     #发布内容
        self.pushButton.setText('发布中...')
        self.pushButton.setEnabled(False)
        self.context = self.textEdit.toPlainText()
        self.author = self.lineEdit.text()
        if self.checkBox.isChecked():
            self.saveName()
        else:
            try:
                remove('savedName')
            except FileNotFoundError:
                pass
        self.thread = sendThread(self.context, self.author)
        self.thread.trigger.connect(self.updateStatus)
        self.thread.start()

    def updateStatus(self, status): #发布后界面更新
        if status == 201:
            self.label_2.setText('发布成功 ( •̀ ω •́ )✧')
            self.textEdit.selectAll()
            if self.checkBox_2.isChecked():
                self.textEdit.clear()
        else:
            self.label_2.setText('发布失败 (っ °Д °;)っ')
            print(status)
        self.textEdit.setFocus()
        self.pushButton.setText('发布')
        self.pushButton.setEnabled(True)
        self.thread.wait()

    def updateText(self, text): #获取剪贴板内容后文本更新
        self.textEdit.setText(text)

    def charCount(self):        #字数统计
        cnt = len(self.textEdit.toPlainText())
        self.cnt.setText(str(cnt))

    def toggleMonitor(self):    #剪贴板监控开关
        if self.checkBox_3.isChecked():
            self.textEdit.setText(paste())
            self.clipMonitor = ClipThread()
            self.clipMonitor.trigger.connect(self.updateText)
            self.clipMonitor.start()
        else:
            self.clipMonitor.quit()
        self.textEdit.setFocus()

    def updateTable(self):      #表格内容更新
        self.refreshButton.setEnabled(False)
        self.refreshButton.setText('刷新中')
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(self.lineNum)
        self.tabThread = tableThread(self.skip, self.lineNum)
        self.tabThread.trigger.connect(self.insertTable)
        self.tabThread.start()

    def insertTable(self, lis): #生成表格与状态更新
        self.refreshButton.setText('刷新')
        self.refreshButton.setEnabled(True)
        self.conNum = lis['count']
        self.label_4.setText('共 %d 条 每页' % (self.conNum))
        self.maxPage = ceil(self.conNum / self.lineNum)
        self.label_3.setText('/%d 页' % (self.maxPage))
        self.spinBox.setMaximum(self.maxPage)
        num = 0
        result = lis['results']
        for row in result:
            self.insertRow(row, num)
            num += 1

    def insertRow(self, row, num):
        for col in range(0, 3):
            string = row[diction[col]]
            if col == 0:
                string = unescape(string)
                string = string.replace('<br>',' ')
            elif col == 2:
                string = str(Communicate.convertFromUTC(string))
                string = string[:16]
            item = QTableWidgetItem(string)
            self.tableWidget.setItem(num, col, item)

    def copyToClip(self, row, col): #双击复制
        item = self.tableWidget.item(row, col)
        copy(item.text())

    def updateListNum(self, num):   #页码变更
        self.skip = (num - 1) * self.lineNum
        self.updateTable()

    def keyPressEvent(self, event): #监听 Ctrl+Enter 快捷键以发布
        if self.textEdit.hasFocus():
            if str(event.key() == '16777249'):
                if str(event.key()) == '16777221' or str(event.key()) == '16777220':
                    self.pushButton.click()

    def setMaximum(self):
        self.spinBox.setValue(self.maxPage)

    def setMinimum(self):
        self.spinBox.setValue(1)

    def updateNum(self, num):   #每页显示数量更新
        num = ''.join(list(filter(str.isdigit, num)))
        if num == '':
            return
        self.lineNum = int(num)
        self.updateTable()

if __name__ == '__main__':
    mainApp = QApplication(sys.argv)
    MainWindow = Window()
    MainWindow.show()
    sys.exit(mainApp.exec_())

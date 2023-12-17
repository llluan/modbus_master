import threading
import random
from time import sleep, gmtime, strftime
import serial
from serial.serialutil import *
from modbus_tk.defines import *
import serial.tools.list_ports
from communication_modbus import Communication_modbus_rtu
from PyQt5 import QtCore
import pyqtgraph as pg
from Ui_MWin import Ui_MainWindow
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QHBoxLayout,
)


class MainWindow(QMainWindow, Ui_MainWindow):
    singal_getOneData = QtCore.pyqtSignal(str)

    def __init__(self):
        super(QMainWindow, self).__init__()

        # 界面初始化
        self.setup_Ui()
        self.set_graphUi()
        self.statusbar.showMessage("状态：初始化完成")
        self.statusbar.setStyleSheet("color:green")
        self.spinBox_sendTime.setValue(500)
        self.lineEdit_addr_textEditedCB()
        self.lineEdit_addr2_textEditedCB()

        # 变量初始化
        self.checkBox_show2data_flag = 0
        self.data_plotY_data = [[], []]
        self.data_plotX_data = []

        self.data_plotX_index = 0
        self.port_para_dict = {
            "baud": 9600,
            "databits": 8,
            "parity": "N",
            "stopbits": 1,
        }
        self.get_currentPara_modbus()
        print(self.readNum, self.slave, self.FuncCode, self.addr)

        # 信号绑定
        self.connectSignals()
        # 定时器初始化
        self.timer_send = QtCore.QTimer(self)
        self.timer_send.timeout.connect(self.timer_sendCB)

        # 开启串口查询线程
        def port_search_append():
            port_value = []
            port_list = list(serial.tools.list_ports.comports())
            for Index in range(len(port_list)):
                port_value.append(port_list[Index][0])
            # print(port_value)
            for i in range(len(port_value)):
                indexINFO = self.comboBox_serial.findText(
                    port_value[i], QtCore.Qt.MatchFixedString
                )  # 返回目标文本所在的索引，若不存在返回负一
                if 0 > indexINFO:
                    self.comboBox_serial.addItem(port_value[i])

        def port_search_appendThread():
            print("Port thread start")
            while True:
                port_search_append()
                sleep(4)

        threading.Thread(
            group=None, target=port_search_appendThread, daemon=True
        ).start()

    def setup_Ui(self):
        self.setupUi(self)
        self.text_dataView = QPlainTextEdit()
        self.text_dataView.setReadOnly(True)
        self.text_dataView.appendPlainText("这里显示数据")
        self.Layouttext_dataView = QHBoxLayout()
        self.Layouttext_dataView.setObjectName("Layouttext_dataView")
        self.Layouttext_dataView.addWidget(self.text_dataView)
        self.tabWidgetPage_text.setLayout(self.Layouttext_dataView)
        self.Layout_graphShow = QHBoxLayout()
        self.Layout_graphShow.setObjectName("Layout_graphShow")
        self.tabWidgetPage_plot.setLayout(self.Layout_graphShow)

    def set_graphUi(self):
        pg.setConfigOptions(antialias=True, background="w")  # 抗锯齿开 背景白
        self.dym_plot_view = pg.plot()
        self.Widget_plot = self.Layout_graphShow.addWidget(self.dym_plot_view)
        # winLayout_Graph = pg.plot()  # PG widget实例化
        # self.Layout_graphShow.addWidget(winLayout_Graph)  # 将实例化传入layout中

        # # self.dym_plot_view = winLayout_Graph.addPlot(title="波形图")
        # self.dym_plot_view = winLayout_Graph

        self.dym_plot_view.setLabel("left", text="值", color="#000000")
        self.dym_plot_view.showGrid(x=True, y=True)  # 栅格设置函数
        # self.dym_plot_view.setLogMode(x=True, y=True)
        self.dym_plot_view.setLabel("bottom", text="时间")  # x轴设置函数
        self.dym_plot_view.setLimits(
            xMin=0, minXRange=100, minYRange=100, maxYRange=1000
        )

    def dym_plot(self):
        if 50 < self.data_plotX_index:
            self.dym_plot_view.setXRange(
                self.data_plotX_index - 50, self.data_plotX_index + 50
            )
        self.dym_plot_view.plot(
            self.data_plotX_data,
            self.data_plotY_data[0],
            pen="b",
            name="动态波形",
            clear=True,
        )

        if self.checkBox_show2data_flag == 1:
            print("painting NO.2")
            self.dym_plot_view.plot(
                self.data_plotX_data,
                self.data_plotY_data[1],
                pen="r",
                name="动态波形2",
            )

    def connectSignals(self):
        self.pushButton_selectFileSavePath.clicked.connect(
            self.pushButton_selectFileSavePath_clicked_slot
        )
        self.spinBox_sendTime.valueChanged.connect(self.spinBox_sendTime_valueChangedCB)
        self.checkBox_repeat.clicked.connect(self.checkBox_repeat_isCheckedCB)
        self.pushButton_linkToSerial.clicked.connect(
            self.pushButton_linkToSerial_clickedCB
        )
        self.singal_getOneData.connect(self.singal_getOneDataCB)
        self.pushButton_send.clicked.connect(self.pushButton_send_clickedCB)
        self.pushButton_save.clicked.connect(self.pushButton_save_clickedCB)
        self.checkBox_show2data.clicked.connect(self.checkBox_show2data_clickedCB)
        self.lineEdit_addr.textChanged.connect(self.lineEdit_addr_textEditedCB)
        self.lineEdit_addr2.textChanged.connect(self.lineEdit_addr2_textEditedCB)

    def timer_sendCB(self):  # 定时器回调函数
        print("this is timerCB")
        if self.checkBox_repeat.checkState():
            print("checkBox_repeat is checked")
            # Communication_modbus_rtu.execute(
            #     self.modbus,
            #     slave=self.slave,
            #     quantity_of_x=self.readNum,
            #     function_code=self.FuncCode,
            #     starting_address=self.addr,
            # )
            self.pushButton_send_clickedCB()
        else:
            self.timer_send.stop()
            print("wrong in timer_send,stop the timer")

    def pushButton_selectFileSavePath_clicked_slot(self):
        FilePath = QFileDialog.getExistingDirectory(None, "选取文件夹", "c:/")
        self.lineEdit_saveFilePath.setText(FilePath)

    def spinBox_sendTime_valueChangedCB(self):
        time = self.spinBox_sendTime.value()
        self.statusbar.showMessage(
            "time between repeat sent is changed,it's " + str(time)
        )

    def checkBox_repeat_isCheckedCB(self):
        if self.checkBox_repeat.checkState():
            self.pushButton_send.setDisabled(True)
            self.comboBox_funcCode.setDisabled(True)
            self.comboBox_readNum.setDisabled(True)
            self.comboBox_slave.setDisabled(True)
            self.lineEdit_addr.setDisabled(True)
            self.get_currentPara_modbus()
            self.timer_send.start(self.spinBox_sendTime.value())
        else:
            self.timer_send.stop()
            self.pushButton_send.setDisabled(False)
            self.comboBox_funcCode.setDisabled(False)
            self.comboBox_readNum.setDisabled(False)
            self.comboBox_slave.setDisabled(False)
            self.lineEdit_addr.setDisabled(False)

    def pushButton_linkToSerial_clickedCB(self):
        if self.pushButton_linkToSerial.isChecked():
            self.pushButton_send.setEnabled
            self.checkBox_repeat.setCheckable
            print("self.pushButton_linkToSerial.isChecked")
            #  ---------------------------------------
            portName = self.comboBox_serial.currentText()
            self.port_para_dict["baud"] = self.comboBox_baud.currentText()
            self.port_para_dict["databits"] = self.comboBox_byteSize.currentText()
            self.port_para_dict["parity"] = self.comboBox_parity.currentText()
            self.port_para_dict["stopbits"] = self.comboBox_stopbite.currentText()

            self.modbus = Communication_modbus_rtu(
                port=portName, modbusRTU_para_dict=self.port_para_dict
            )
            if 0 > self.modbus.err:  # 出错了
                print("err = -1")
                QMessageBox.information(self, "err=-1", "串口打开失败")

        else:
            self.checkBox_repeat.setChecked(False)
            self.timer_send.stop()  # 定时器关闭，不再触发回调函数,资源回收
            # print("定时器关闭，不能再触发回调函数")
            self.pushButton_send.setDisabled

    def comboBox_serial_currentIndexChangedCB(self):
        print("this is comboBox_serial_currentIndexChangedCB")

    def singal_getOneDataCB(self, data):
        print("get data--->", data, "\n\r")
        # self.text_dataView.setPlainText("get data--->", data+"\n\r")
        self.dym_plot()

    def pushButton_send_clickedCB(self):
        print("pushButton_send_clickedCB")
        if self.checkBox_repeat.checkState():
            self.get_currentPara_modbus()
            # print(self.checkBox_repeat.checkState())

        self.data = self.modbus.execute(
            slave=self.slave,
            quantity_of_x=self.readNum,
            function_code=self.FuncCode,
            starting_address=self.addr,
        )
        self.data_plotY_data[0].append(self.data[0])
        str_emit = str(self.data[0])

        if self.checkBox_show2data.checkState():
            self.data2 = self.modbus.execute(
                slave=self.slave,
                quantity_of_x=self.readNum,
                function_code=self.FuncCode,
                starting_address=self.addr2,
            )
            # self.data_plotY2_data.append(self.data2[0])
            self.data_plotY_data[1].append(self.data2[0])
            str_emit = str_emit.join(str(self.data2[0]))

        # print("data1 data2: ", int(self.data_plotY_data))
        self.data_plotX_data.append(self.data_plotX_index)
        self.data_plotX_index += 1
        self.singal_getOneData.emit(str_emit)
        # # 数据生成(debug)
        # threading.Thread(
        #     group=None, target=self.generate_dataThread, daemon=True
        # ).start()

    def pushButton_save_clickedCB(self):
        print("this is pushButton_save_clickedCB")
        filePath = self.lineEdit_saveFilePath.text()
        time = gmtime()
        name = strftime("%Y-%m-%d_%H_%M_%S", time)
        filenamePath = filePath + "/" + name + ".txt"
        f = open(filenamePath, "w")
        f.write(str(self.data_plotY_data))

    def get_currentPara_modbus(self):
        self.readNum = int(self.comboBox_readNum.currentText())
        self.slave = int(self.comboBox_slave.currentText())
        self.FuncCode = globals()[self.comboBox_funcCode.currentText()]
        self.addr = int(self.lineEdit_addr.text(), 16)
        self.addr2 = int(self.lineEdit_addr2.text(), 16)

    def checkBox_show2data_clickedCB(self):
        if self.checkBox_show2data.isChecked():
            self.lineEdit_addr2.setEnabled(True)
            self.checkBox_show2data_flag = 1
        else:
            self.lineEdit_addr2.setEnabled(False)
            self.checkBox_show2data_flag = 0

    def lineEdit_addr_textEditedCB(self):
        try:
            text_inaddr = int(self.lineEdit_addr.text(), 16)
            self.lineEdit_addrTransTobin.setText(bin(text_inaddr))
        except:
            print("是否地址格式非法？")

    def lineEdit_addr2_textEditedCB(self):
        try:
            text_inaddr = int(self.lineEdit_addr.text(), 16)
            self.lineEdit_lineEdit_addrTransTobin2.setText(bin(text_inaddr))
        except:
            print("是否地址格式非法？")

    # -----------------------debug------------------------------------------------------

    def process_data_Modbus():
        pass

    def generate_data(self):
        self.data_plotX_data.append(self.data_plotX_index)
        self.data_plotX_index += 1
        self.data_plotY_data.append(random.randint(20, 100))

    def generate_dataThread(self):  # only for Debug
        while True:
            self.generate_data()
            print(self.data_plotY_data)
            self.singal_getOneData.emit(self.data_plotY_data[-1])
            sleep(1)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    # app.setAttribute(QtCore.Qt.AA_Use96Dpi)
    mainwin = MainWindow()
    mainwin.show()
    sys.exit(app.exec_())

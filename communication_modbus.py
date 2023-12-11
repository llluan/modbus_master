from modbus_tk import modbus_rtu
from modbus_tk.defines import *
import serial
from time import sleep
import queue
import threading


class Communication_modbus_rtu(object):
    def __init__(self, port, modbusRTU_para_dict):
        self.err = 0
        self.buffer_recv_dataqueue = queue.Queue(0)  # 注意为了防止数据丢失，队列设置成无限大
        print(
            port,
            modbusRTU_para_dict,
        )
        try:
            # self.serial = serial.Serial(
            #     port,
            #     baudrate=modbusRTU_para_dict["baud"],
            #     bytesize=modbusRTU_para_dict["bytesize"],
            #     stopbits=modbusRTU_para_dict["stopbite"]
            # )

            print("success to open")
            self.master = modbus_rtu.RtuMaster(
                serial.Serial(
                    port,
                    # baudrate=9600,
                    # bytesize=8,
                    # parity='N',
                    # stopbits=1,
                    # xonxoff=0,
                )
            )
            self.master.set_timeout(1.0)
            print("RTU master config done")
        except:
            print("open serial fail")
            self.err = -1

    def execute(
        self, slave, function_code, starting_address, quantity_of_x
    ):  # Modbus使能
        # try:
        #     print("enable execute success")
        #     print(slave, function_code, starting_address, quantity_of_x)
        #     data = self.master.execute(
        #         slave=slave, function_code=function_code, starting_address=starting_address, quantity_of_x=quantity_of_x
        #     )
        #     self.buffer_recv_dataqueue.join(data)
        #     self.buffer_recv_dataqueue.join(data)
        #     data = "DEVICE--->PC " + data
        #     print(data)
        # except:
        #     print("execute failed")
        #     print("enable execute success")
        try:
            print(slave, function_code, type(starting_address), quantity_of_x)
            data = self.master.execute(
                slave=slave,
                function_code=function_code,
                starting_address=starting_address,
                quantity_of_x=quantity_of_x,
            )
            print("data:", data)
            return data
        except:
            print("execute wrong")

    # 在 modbusRTU 协议中不应该当使用以下线程，因为下位机并不需要自发地向上位机发送数据
    def __thread_set(
        self, slave, function_code, starting_address, quantity_of_x, time_sleep
    ):
        print("modbus thread set start")
        while True:
            try:
                data = self.master.execute(
                    slave, function_code, starting_address, quantity_of_x
                )
                self.buffer_recv_dataqueue.join(data)
                data = "DEVICE--->PC " + data
                print(data)
                sleep(time_sleep / 1000)
            except:
                print("execute failed")
                break

    def modbusRTU_threadStart(self):
        thread = threading.Thread(target=self.threadset, daemon=True)
        thread.start()

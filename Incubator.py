import serial
import time
import os
def get_Incubator_port(n=3):
    for i in range(0, n):
        path = "/dev/ttyUSB{}".format(i)
        #print(path)
        if os.path.exists(path):
            serialPort = serial.Serial(port=path, baudrate=2400, timeout=2)
            serialPort.write(b"IN PV 01\r\n")
            time.sleep(1)
            if serialPort.in_waiting > 0:
                serialString = serialPort.read_all()
                str = serialString.decode("Ascii")
                serialPort.close()
                #print(str)
                if str.find("OK") != -1:
                    return path
            else:
                serialPort.close()

    return None


class Incubator:
    def __init__(self, port, timeout=1.0):
        self.timeout = timeout
        self.serialPort = serial.Serial(
        port=port,
        baudrate=2400,
        bytesize=8,
        timeout=2,
        stopbits=serial.STOPBITS_ONE,
        )


    def get_parameter(self, cmd):
        serialString = ""  # Used to hold data coming over UART
        self.serialPort.write(cmd)  # b"IN PV 01\r\n"
        time.sleep(self.timeout)
        if self.serialPort.in_waiting > 0:
            serialString = self.serialPort.read_all()
            list = serialString.splitlines()
            if len(list) == 2:
                if list[0].decode("Ascii").find("OK") != -1:
                    if list[1].decode("Ascii").replace('.','',1).isdigit():
                        return float(list[1].decode("Ascii"))
                    else:
                        print("Second Line must be number\n")
                        return None
                else:
                    print("First Line must be 'OK'\n")
                    return None
            else:
                print("Response must be two lines\n")
                return None
        else:
            print("No Response after {} sec\n".format(self.timeout))
            return None


    def get_Temperature(self):
        return self.get_parameter(b"IN PV 01\r\n")


    def get_Co2(self):
        return self.get_parameter(b"IN PV 02\r\n")


    def get_Humidity(self):
        return self.get_parameter(b"IN PV 03\r\n")

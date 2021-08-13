import serial
import time
import os

def get_port(req, resp, prefix="/dev/ttyUSB",n=3, baudrate=2400):
    for i in range(0, n):
        path = prefix + "{}".format(i)
        #print(path)
        if os.path.exists(path):
            serialPort = serial.Serial(port=path, baudrate=baudrate, timeout=2)
            serialPort.write(req)
            time.sleep(1)
            if serialPort.in_waiting > 0:
                serialString = serialPort.read_all()
                str = serialString.decode("Ascii")
                serialPort.close()
                #print(str)
                if str.find(resp.decode("Ascii")) != -1:
                    return path
            else:
                serialPort.close()

    return None


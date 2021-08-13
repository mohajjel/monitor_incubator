import serial
import time
import os

def get_port(req, resp, prefix="/dev/ttyUSB",n=[0,1,2], baudrate=2400):
    for i in n:
        path = prefix + "{}".format(i)
        #print(path)
        if os.path.exists(path):
            serialPort = serial.Serial(port=path, baudrate=baudrate, timeout=2)
            serialPort.write(req)
            time.sleep(1)
            if serialPort.in_waiting > 0:
                try:
                    serialString = serialPort.read_all()
                    str = serialString.decode("Ascii")
                    print(str)
                    serialPort.close()
                    #print(str)
                
                    if str.find(resp.decode("Ascii")) != -1:
                        return i
                except:
                    serialPort.close()
            else:
                serialPort.close()

    return None


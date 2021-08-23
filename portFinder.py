import serial
import time
import os

def get_port(req, resp, list_ports, baudrate=2400):
    for i in range(len(list_ports)):
        #path = prefix + "{}".format(i)
        path = list_ports[i];
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


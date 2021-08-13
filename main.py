# Python program to illustrate the concept
# of threading
# importing the threading module
import threading
import time
import gsm
import Incubator
import portFinder
import config
from constants import PATH
from constants import CONFIG_FILE_NAME
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import subprocess

hostName = "0.0.0.0"  # "localhost"
serverPort = 8889


class Status:
    gsm_is_connected = False
    incubator_is_connected = False
    T = 0.0
    H = 0.0
    Co2 = 0.0
    def __init__(self):
        self.lock = threading.Lock()
    def get(self, param_name):
        self.lock.acquire()
        if param_name == "T":
            v = self.T
        elif param_name == "H":
            v = self.H
        elif param_name == "Co2":
            v = self.Co2
        elif param_name == "gsm_is_connected":
            v = self.gsm_is_connected
        
        elif param_name == "incubator_is_connected":
            v = self.incubator_is_connected
        else:
            raise Exception("Invalid param name")
        
        self.lock.release()
        return v

    def set(self, param_name, param_val):
        self.lock.acquire()
        if param_name == "T":
            self.T = param_val
        elif param_name == "H":
            self.H = param_val
        elif param_name == "Co2":
            self.Co2 = param_val
        elif param_name == "gsm_is_connected":
            self.gsm_is_connected = param_val     
        elif param_name == "incubator_is_connected":
            self.incubator_is_connected = param_val
        else:
            raise Exception("Invalid param name")
        self.lock.release()



def monitor():
    global status
    configs = config.read_config(PATH + CONFIG_FILE_NAME)
    phone_numbers = configs["params"]["phone_numbers"]
    apn = "mcinet"  # configs["params"]["apn"] #

    Tmin = float(configs["params"]["Tmin"])
    Tmax = float(configs["params"]["Tmax"])

    Co2min = float(configs["params"]["Co2min"])
    Co2max = float(configs["params"]["Co2max"])

    Hmin = float(configs["params"]["Hmin"])
    Hmax = float(configs["params"]["Hmax"])

    Period = 5.0

    gsm_port = portFinder.get_port(b"AT\r\n", b"OK")
    if gsm_port == None:
        raise Exception("GSM not Connected")
    status.set("gsm_is_connected", True)
    print("GSM port is {}".format(gsm_port))
    mgsm = gsm.myGSM(gsm_port, apn, phone_numbers)

    incubator_port = portFinder.get_port(b"IN PV 01\r\n", b"OK")
    if incubator_port == None:
        mgsm.send_message_for_all("Error Incubutor is not connected")
        raise Exception("Incubutor not Connected")
    status.set("incubator_is_connected", True)
    print("Incubutor port is {}".format(incubator_port))
    incubator = Incubator.Incubator(incubator_port, 1.0)

    mgsm.send_message_for_all("Hello System is OK!")

    # All thinges are ok
    serialString = ""  # Used to hold data coming over UART

    n_NoResponse = 0
    while True:
        configs = config.read_config(PATH + CONFIG_FILE_NAME)
        phone_numbers = configs["params"]["phone_numbers"]
        apn = "mcinet"  # configs["params"]["apn"] #

        Tmin = float(configs["params"]["Tmin"])
        Tmax = float(configs["params"]["Tmax"])

        Co2min = float(configs["params"]["Co2min"])
        Co2max = float(configs["params"]["Co2max"])

        Hmin = float(configs["params"]["Hmin"])
        Hmax = float(configs["params"]["Hmax"])
        temperature = float(incubator.get_Temperature())
        status.set("T", temperature)
        if temperature == None:
            print("ERROR:No Response")
            n_NoResponse += 1
        else:
            print("T={}\n".format(temperature))
            if temperature < Tmin or temperature > Tmax:
                mgsm.send_message_for_all(
                    "Warning: T={} is out of range".format(temperature)
                )

        time.sleep(1.0)

        co2 = incubator.get_Co2()
        status.set("Co2", co2)
        if co2 == None:
            print("ERROR:No Response")
            n_NoResponse += 1
        else:
            print("Co2={}\n".format(co2))
            if co2 < Co2min or co2 > Co2max:
                mgsm.send_message_for_all("Warning: Co2={} is out of range".format(co2))

        time.sleep(1.0)

        humidity = incubator.get_Humidity()
        status.set("H", humidity)
        if humidity == None:
            print("ERROR:No Response")
            n_NoResponse += 1
        else:
            print("H={}\n".format(humidity))
            if humidity < Hmin or humidity > Hmax:
                mgsm.send_message_for_all(
                    "Warning: H={} is out of range".format(humidity)
                )

        if n_NoResponse == 3:
            mgsm.send_message_for_all("ERROR: Incubutor is not connected")
            n_NoResponse = 0

        # mgsm.gsm.sms.readAll()

        # index = mgsm.gsm.sms.newMessageIndex(0)
        # if index > 0:
        #    strr = mgsm.gsm.sms.readSMS(index)

        time.sleep(Period)


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.path)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(PATH + "setting.html") as f:
            lines = f.read()
            self.wfile.write(bytes(lines, encoding="utf8"))

    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "text/json")
        self.end_headers()
        if self.path == "/get_config":
            # self._set_headers()
            """
            jsonData = {
                "ver": "1.0",
                "status": "200",
                "result": {
                    "Tmin": "5.0",
                    "Tmax": "40.0",
                    "Co2min": "80.0",
                    "Co2max": "100.0",
                    "Hmin": "70.0",
                    "Hmax": "90.0",
                    "PNumber1": "09196152542",
                    "PNumber2": "09196152542",
                    "PNumber3": "09196152542",
                    "PNumber4": "",
                },
            }
            """
            jsonData = config.read_config(PATH + CONFIG_FILE_NAME)
            self.wfile.write(bytes(json.dumps(jsonData), encoding="utf8"))
        elif self.path == "/get_status":
            # self._set_headers()
            
            jsonData = {
                "ver": "1.0",
                "status": "200",
                "params": {

                }
            }
            
            jsonData["params"]["T"] = status.get("T")
            jsonData["params"]["H"] = status.get("H")
            jsonData["params"]["Co2"] = status.get("Co2")
            jsonData["params"]["gsm_is_connected"] = status.get("gsm_is_connected")
            jsonData["params"]["incubator_is_connected"] = status.get("incubator_is_connected")


            

            #jsonData = config.read_config(PATH + CONFIG_FILE_NAME)
            self.wfile.write(bytes(json.dumps(jsonData), encoding="utf8"))
        elif self.path == "/change_information":
            print("RRRRRRRRRRRRRRRRR")
            length = int(self.headers.get("content-length"))
            message = json.loads(self.rfile.read(length))
            config.write_config(PATH+CONFIG_FILE_NAME, message)
            print(json.dumps(message))
        elif self.path == "/reset_board":
            subprocess.call(['reboot','now'])
        elif self.path == "/shutdown_board":
            subprocess.call(['shutdown','now'])
        elif self.path == "/update_firmware":
            subprocess.call(['git','pull'])
        
        print(self.path)



def server():
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")


def thread_monitor(num):
    """
    function to print cube of given num
    """
    print("Cube: {}".format(num * num * num))
    monitor()


def thread_server(num):
    """
    function to print square of given num
    """
    server()
    print("Square: {}".format(num * num))


if __name__ == "__main__":
    global status
    status = Status()  
    # creating thread
    t1 = threading.Thread(target=thread_server, args=(10,))
    t2 = threading.Thread(target=thread_monitor, args=(10,))

    # starting thread 1
    t1.start()
    # starting thread 2
    t2.start()

    # wait until thread 1 is completely executed
    t1.join()
    # wait until thread 2 is completely executed
    t2.join()

    # both threads completely executed
    print("Done!")
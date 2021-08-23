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
import os
import sys
import ups

hostName = "0.0.0.0"  # "localhost"
serverPort = 80
#sys.stdout = open('/home/pi/monitor_incubator/log3.txt', 'w')

class Logger:
 
    def __init__(self, filename):
        self.console = sys.stdout
        self.file = open(filename, 'w')
 
    def write(self, message):
        self.console.write(message)
        self.file.write(message)
        self.file.flush()
 
    def flush(self):
        self.console.flush()
        self.file.flush()
 
path = '/home/pi/monitor_incubator/log4.txt'
sys.stdout = Logger(path)
print('Hello, World')

lock = threading.Lock()

class Status:
    gsm_is_connected = False
    incubator_is_connected = False
    ups_is_connected = False
    battrey_capacity = 0
    power_is_plugged = False
    vout = 0.0
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

        elif param_name == "ups_is_connected":
            v = self.ups_is_connected
        elif param_name == "battrey_capacity":
            v = self.battrey_capacity
        elif param_name == "vout":
            v = self.vout
        elif param_name == "power_is_plugged":
            v = self.power_is_plugged
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
        elif param_name == "ups_is_connected":
            self.ups_is_connected = param_val
        elif param_name == "battrey_capacity":
            self.battrey_capacity = param_val
        elif param_name == "vout":
            self.vout = param_val
        elif param_name == "power_is_plugged":
            self.power_is_plugged = param_val

        else:
            raise Exception("Invalid param name")
        self.lock.release()


def monitor():
    global status
    mgsm = None
    configs = config.read_config(PATH + CONFIG_FILE_NAME)
    phone_numbers = configs["params"]["phone_numbers"]
    apn = "mcinet"  # "mtnirancell"#  # configs["params"]["apn"] #

    Tmin = float(configs["params"]["Tmin"])
    Tmax = float(configs["params"]["Tmax"])

    Co2min = float(configs["params"]["Co2min"])
    Co2max = float(configs["params"]["Co2max"])

    Hmin = float(configs["params"]["Hmin"])
    Hmax = float(configs["params"]["Hmax"])

    Period = 5.0
    n = [0, 1, 2]
    stream = os.popen('ls /dev/ttyUSB*')
    list_ports = stream.read().split('\n')
    list_ports = list_ports[:-1]

    gsm_port_idx = portFinder.get_port(b"AT\r\n", b"OK", list_ports)
    if gsm_port_idx == None:
        print("GSM not Connected")
        # raise Exception("GSM not Connected")
        status.set("gsm_is_connected", False)
        # return -1
    else:
        status.set("gsm_is_connected", True)
        print("GSM port is {}".format(list_ports[gsm_port_idx]))
        mgsm = gsm.myGSM(list_ports[gsm_port_idx], apn, phone_numbers)
        list_ports.pop(gsm_port_idx)
    incubator_port_idx = portFinder.get_port(b"IN PV 01\r\n", b"OK", list_ports)
    if incubator_port_idx == None:
        # mgsm.send_message_for_all("Error Incubutor is not connected")
        status.set("incubator_is_connected", False)
        print("Incubutor not Connected")
        # raise Exception("Incubutor not Connected")
        # return -1
    else:
        status.set("incubator_is_connected", True)
        print("Incubutor port is {}".format(list_ports[incubator_port_idx]))
        incubator = Incubator.Incubator(list_ports[incubator_port_idx], 1.0)
        list_ports.pop(incubator_port_idx)
    ups_port_idx = portFinder.get_port(b"", b"SmartUPS",list_ports, baudrate=9600)
    if ups_port_idx == None:
        status.set("ups_is_connected", False)
        print("UPS not Connected")
        # raise Exception("UPS not Connected")
        # return -1
    else:
        status.set("ups_is_connected", True)
        print("UPS port is {}".format(list_ports[ups_port_idx]))
        my_ups = ups.UPS2(list_ports[ups_port_idx])

    if ups_port_idx != None and gsm_port_idx != None: #and incubator_port_idx != None:
        print("All thinges ok send sms:")
        mgsm.send_message_for_all("Hello System is On!")
        n_NoResponse = 0
        print("monitor loop")
        T_out_of_range = "T_out_of_range"
        Co2_out_of_range = "Co2_out_of_range"
        Co2_capsule_is_not_connected = "Co2_capsule_is_not_connected"
        H_out_of_range = "H_out_of_range"
        Power_failure = "Power_failure"
        Incubatur_not_connected = "Incubatur_not_connected"
        notifications = {
            T_out_of_range: False,
            Co2_out_of_range: False,
            Co2_capsule_is_not_connected: False,
            H_out_of_range: False,
            Power_failure: False,
            Incubatur_not_connected: False,
        }
        flag_send_warning_T = True
        flag_send_warning_H = True
        flag_send_warning_CO2 = True
        flag_send_warning_Power = True
        flag_send_warning_Incubator = True
        reconnect_to_incubator = False;
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
            
            try:
                #print('*******************')
                #print(os.path.exists(f"/dev/ttyUSB{incubator_port_idx}"))
                if reconnect_to_incubator:
                    print("try to reconnect to incubator...")
                    stream = os.popen('ls /dev/ttyUSB*')
                    list_ports = stream.read().split('\n')
                    list_ports = list_ports[:-1]
                    list_ports.remove(mgsm.path_gsm)
                    list_ports.remove(my_ups.port)
                    incubator_port_idx = portFinder.get_port(b"IN PV 01\r\n", b"OK", list_ports)
                    if incubator_port_idx!=None:
                        status.set("incubator_is_connected", True)
                        print("Incubutor port is {}".format(list_ports[incubator_port_idx]))
                        incubator = Incubator.Incubator(list_ports[incubator_port_idx], 1.0)
                        reconnect_to_incubator = False
                        print("Ok")
                    else:
                        print("Failed")
                        raise Exception("Incubator not connected!(3)")
                    
                lock.acquire()

                temperature = incubator.get_Temperature()
                status.set("T", temperature)
                if temperature == None:
                    print("ERROR:No Response")
                    n_NoResponse += 1
                    status.set("incubator_is_connected", False)
                else:
                    n_NoResponse = 0
                    status.set("incubator_is_connected", True)
                    print("T={}\n".format(temperature))
                    if flag_send_warning_T and (temperature < Tmin or temperature > Tmax):
                        mgsm.send_message_for_all(
                            "Warning: T={} is out of range".format(temperature)
                        )

                time.sleep(0.1)

                co2 = incubator.get_Co2()
                status.set("Co2", co2)
                if co2 == None:
                    print("ERROR:No Response")
                    n_NoResponse += 1
                    status.set("incubator_is_connected", False)
                else:
                    n_NoResponse = 0
                    status.set("incubator_is_connected", True)
                    print("Co2={}\n".format(co2))
                    if flag_send_warning_CO2 and co2 > 99.8:
                        mgsm.send_message_for_all(
                            "Warning: Co2 capsule is not connected".format(co2)
                        )
                    if flag_send_warning_CO2 and (co2 < Co2min or co2 > Co2max):
                        mgsm.send_message_for_all(
                            "Warning: Co2={} is out of range".format(co2)
                        )

                time.sleep(0.1)

                humidity = incubator.get_Humidity()
                status.set("H", humidity)
                if humidity == None:
                    print("ERROR:No Response")
                    n_NoResponse += 1
                    status.set("incubator_is_connected", False)
                else:
                    n_NoResponse = 0
                    status.set("incubator_is_connected", True)
                    print("H={}\n".format(humidity))
                    if flag_send_warning_H and (humidity < Hmin or humidity > Hmax):
                        mgsm.send_message_for_all(
                            "Warning: H={} is out of range".format(humidity)
                        )
                lock.release()
            except:
                print("Incubatur is not connected(2)")
                reconnect_to_incubator = True
                n_NoResponse += 1
            lock.acquire()
            if flag_send_warning_Incubator and n_NoResponse != 0:
                mgsm.send_message_for_all("ERROR: Incubutor is not connected")
                mgsm.dial_all_numbers()
                n_NoResponse = 0

            print(my_ups.decode_uart())

            status.set("battrey_capacity", my_ups.batcap)
            if my_ups.vin[0] == "GOOD":
                status.set("power_is_plugged", True)
            else:
                status.set("power_is_plugged", False)
                if flag_send_warning_Power:
                    mgsm.send_message_for_all("ERROR: power failure!")
                    mgsm.dial_all_numbers()
            status.set("vout", my_ups.vout)

            data = mgsm.gsm.sms.readAll()
            if data.lower().find("get") != -1:
                mgsm.send_message_for_all(
                    "T={} Co2={} H={} Power is plugged={}".format(
                        status.get("T"),
                        status.get("Co2"),
                        status.get("H"),
                        status.get("power_is_plugged"),
                    )
                )
            elif data.lower().find("off all") != -1:
                flag_send_warning_T = False
                flag_send_warning_H = False
                flag_send_warning_CO2 = False
                flag_send_warning_Power = False
                flag_send_warning_Incubator = False

                print("warning all off")

            elif data.lower().find("off t") != -1:
                flag_send_warning_T = False
                print("warning T off")
            elif data.lower().find("off h") != -1:
                flag_send_warning_H = False
                print("warning H off")
            elif data.lower().find("off co2") != -1:
                flag_send_warning_CO2 = False
                print("warning CO2 off")
            elif data.lower().find("off power") != -1:
                flag_send_warning_Power = False
                print("warning power off")
            elif data.lower().find("off inc") != -1:
                flag_send_warning_Incubator = False
                print("warning incubator off")

            elif data.lower().find("on t") != -1:
                flag_send_warning_T = True
                print("warning T on")
            elif data.lower().find("on h") != -1:
                flag_send_warning_H = True
                print("warning H on")
            elif data.lower().find("on co2") != -1:
                flag_send_warning_CO2 = True
                print("warning CO2 on")
            elif data.lower().find("on power") != -1:
                flag_send_warning_Power = True
                print("warning power on")
            elif data.lower().find("on inc") != -1:
                flag_send_warning_Incubator = True
                print("warning incubator on")
            elif data.lower().find("on all") != -1:
                flag_send_warning_T = True
                flag_send_warning_H = True
                flag_send_warning_CO2 = True
                flag_send_warning_Power = True
                flag_send_warning_Incubator = True
                print("warning all on")

            # index = mgsm.gsm.sms.newMessageIndex(0)
            # if index > 0:
            #    strr = mgsm.gsm.sms.readSMS(index)
            lock.release()
            time.sleep(Period)

    else:
        print("Error")
        return -1


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.path)

        self.send_response(200)

        if self.path == "/log":
            self.send_header("Content-type", "text/plain")
            self.end_headers()           
            with open(PATH + "log4.txt") as f:
                lines = f.read()
                self.wfile.write(bytes(lines, encoding="utf8"))
                f.close()            
        else:
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open(PATH + "setting.html") as f:
                lines = f.read()
                self.wfile.write(bytes(lines, encoding="utf8"))
                f.close()

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

            jsonData = {"ver": "1.0", "status": "200", "params": {}}

            jsonData["params"]["T"] = status.get("T")
            jsonData["params"]["H"] = status.get("H")
            jsonData["params"]["Co2"] = status.get("Co2")
            jsonData["params"]["gsm_is_connected"] = status.get("gsm_is_connected")
            jsonData["params"]["incubator_is_connected"] = status.get(
                "incubator_is_connected"
            )
            jsonData["params"]["ups_is_connected"] = status.get("ups_is_connected")
            jsonData["params"]["vout"] = status.get("vout")
            jsonData["params"]["battrey_capacity"] = status.get("battrey_capacity")
            jsonData["params"]["power_is_plugged"] = status.get("power_is_plugged")

            # jsonData = config.read_config(PATH + CONFIG_FILE_NAME)
            self.wfile.write(bytes(json.dumps(jsonData), encoding="utf8"))
        elif self.path == "/change_information":
            print("RRRRRRRRRRRRRRRRR")
            length = int(self.headers.get("content-length"))
            message = json.loads(self.rfile.read(length))
            config.write_config(PATH + CONFIG_FILE_NAME, message)
            print(json.dumps(message))
        elif self.path == "/reset_board":
            lock.acquire()
            subprocess.call(["reboot", "now"])
            #lock.release()
        elif self.path == "/shutdown_board":
            subprocess.call(["shutdown", "now"])
        elif self.path == "/update_firmware":
            stream = os.popen('git pull')
            output = stream.read()
            #if output.find('Already up to date')!=-1
            if output.find('Updating')!=-1:
                lock.acquire()
                print("restart")
                time.sleep(1)
                subprocess.call(["reboot", "now"])
            elif output.find('Already up to date')!=-1:
                print("Already up to date")
            else:
                print("update failed")
            """
            cmd = subprocess.Popen(['git', 'pull'], stdout=subprocess.PIPE)
            cmd_out, cmd_err = cmd.communicate()
            print("out->",cmd_out)
            print("error->",cmd_err)

            #r = subprocess.call(['git','pull'],stdout=str.)
            if cmd_out == b"Already up to date.\n":
                print("->Already up to date.")
            elif cmd_out.decode("Ascii").find("fatal") != -1:
                print(cmd_out)
                print(cmd_err)

                #os.execv(sys.argv[0], sys.argv)
            """
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

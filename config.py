import json
import threading
lock = threading.Lock()
def read_config(path):
    lock.acquire()
    f=open(path, "r")
    data = json.load(f)
    f.close()
    lock.release()
    return data
def write_config(path,message):
    lock.acquire()
    f=open(path, "w")
    f.write(json.dumps(message, indent=4))
    f.close()
    lock.release()


data = read_config('/home/pi/monitor_incubator/'+'config.json')
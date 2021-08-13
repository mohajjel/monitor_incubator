from usim800 import sim800
import serial
import time

import mysms

class myGSM:
    def __init__(self, gsm_port, apn, phone_numbers):
        self.path_gsm = gsm_port
        if self.path_gsm == None:
            print("GSM modem not connected!")
            raise Exception("GSM modem not connected!")
        self.gsm = sim800(baudrate=2400, path=self.path_gsm)
        #self.gsm.sms = mysms.mysms(baudrate=self.gsm._baudrate,path=self.gsm._path)
        self.gsm.requests.APN = apn
        self.phone_numbers = phone_numbers
        

    def send_message_for_all(self, msg, ntry=1):
        list_flag = [False] * len(self.phone_numbers)
        for j in range(ntry):
            for i in range(len(self.phone_numbers)):
                if not(list_flag[i]):
                    if self.gsm.sms.send(self.phone_numbers[i], msg):
                        list_flag[i]=True;
            if all(flag for flag in list_flag):
                break
            time.sleep(10)


'''
        message = "Hello"

        if path_device != None:
            message = message + " Device Connected."
        else:
            message = message + " Device Not Connected."


'''
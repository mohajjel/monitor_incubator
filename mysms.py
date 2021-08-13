
from usim800.Communicate import communicate


class mysms(communicate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def send(self, number, sms):
        cmd = "AT"
        self._send_cmd(cmd)
        cmd = "AT+CMGF=1"
        # Sets the GSM Module in Text Mode
        self._send_cmd(cmd)
        cmd = 'AT+CMGS="{}"'.format(number)
        self._send_cmd(cmd)
        SMS = sms
        self._send_cmd(SMS,t=0.5)
        cmd = "\x1A"
        self._send_cmd(cmd,t=0.1)
        cmd = "AT +SAPBR=0,1"
        data = self._send_cmd(cmd,return_data=True,t=0.5)
        try:
            stats = (data.decode().split()[-1])
            if "OK" in stats:
                stats = True
        except:
            stats = False
        return stats

    def readAll(self,index=None):
        print("OOOOOOOOOOOOOOOOOOOOOO")
        self._send_cmd('AT+CPMS="ME","ME","ME"',read=False)
        cmd = "AT"
        self._send_cmd(cmd)
        cmd = "AT+CMGF=1"
        # Sets the GSM Module in Text Mode
        self._send_cmd(cmd)
        
        cmd = 'AT+CMGL=\"ALL\"' # 'AT+CMGL="ALL"'
        print(cmd)
        self._send_cmd(cmd,t=2)
        data = self._readtill("OK")
        print(data)
        
        cmd='AT+CMGDA=\"DEL ALL\"'
        print(cmd)
        print(self._send_cmd(cmd))
        return data
    def newMessageIndex(self, mode):
        self._send_cmd("+CMGF=1")
        h = self._send_cmd("+CMGL=\"REC UNREAD\",1", t=3)
        if h != None:
            i = 0
            if mode:
                i  = h.index("+CMGL: ")
            else:
                i  = h.rindex("+CMGL: ")        
            index=int(h[i+7:i+9])
            if index<=0:
                return 0
            return index
        else:
            return 0
    def readSMS(self, index, changeStatusToRead = True):
        self._send_cmd("+CMGF=1")
        resp = self._send_cmd("+CMGR={},{}".format(index, int(not(changeStatusToRead)))) 
        h=""
        resp = resp[resp.find('\n'):]
        resp = resp[resp.find('\n'):]
        h=resp[:resp.find('\n')]
        return h


from usim800.Communicate import communicate


class sms(communicate):
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
        self._send_cmd("AT", printio=True)
        self._send_cmd('AT+CPMS="ME","ME","ME"', printio=True)
        
        # Sets the GSM Module in Text Mode
        self._send_cmd("AT+CMGF=1",printio=True)
        
        self._send_cmd('AT+CMGL=\"ALL\"', read=False)
        data = self._readtill("OK")
        print(data)
        
        self._send_cmd('AT+CMGDA=\"DEL READ\"', printio=True)
        return data
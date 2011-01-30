
import httplib, urllib

class Getter:
    
    data = ''
    
    def postRequest(self, host, url, params = {}, headers = {}):
        post_data = urllib.urlencode(params)
        conn = httplib.HTTPConnection(host)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        conn.request('POST', url, post_data, headers)
        response = conn.getresponse()
        if (response.status != 200):
            res = False
        else:
            res = True
        self.status = response.status
        self.data = response.read()
        conn.close()
        return res    
        
import base64
import json
import logging

import requests
from helpers.Parsers.primevideo.remotedevice import RemoteDevice
from pywidevine.decrypt.wvdecryptcustom import WvDecrypt


class license_request:
    def __init__(self):
        """CLASS FOR AMZN License"""
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.host = 'http://wvapi.wvclub.eu.org:6080/'
        self.key = 'tonixxx789'

    def widevine_cert(self, challenge, url, headers):
        pass
        
    def clean_pssh(self, pssh_b64):
        WV_SYSTEM_ID = [237, 239, 139, 169, 121, 214, 74, 206, 163, 200, 39, 220, 213, 29, 33, 237]
        pssh = base64.b64decode(pssh_b64)
        new_pssh = bytearray([0,0,0])
        new_pssh.append(32+len(pssh))
        new_pssh[4:] = bytearray(b'pssh')
        new_pssh[8:] = [0,0,0,0]
        new_pssh[13:] = WV_SYSTEM_ID
        new_pssh[29:] = [0,0,0,0]
        new_pssh[31] = len(pssh)
        new_pssh[32:] = pssh
        return base64.b64encode(new_pssh).decode()


    def _license(self, url, headers, pssh=None, cert=False, device=None):

        cert = "CAUSwgUKvAIIAxIQCuQRtZRasVgFt7DIvVtVHBi17OSpBSKOAjCCAQoCggEBAKU2UrYVOSDlcXajWhpEgGhqGraJtFdUPgu6plJGy9ViaRn5mhyXON5PXmw1krQdi0SLxf00FfIgnYFLpDfvNeItGn9rcx0RNPwP39PW7aW0Fbqi6VCaKWlR24kRpd7NQ4woyMXr7xlBWPwPNxK4xmR/6UuvKyYWEkroyeIjWHAqgCjCmpfIpVcPsyrnMuPFGl82MMVnAhTweTKnEPOqJpxQ1bdQvVNCvkba5gjOTbEnJ7aXegwhmCdRQzXjTeEV2dO8oo5YfxW6pRBovzF6wYBMQYpSCJIA24ptAP/2TkneyJuqm4hJNFvtF8fsBgTQQ4TIhnX4bZ9imuhivYLa6HsCAwEAAToPYW1hem9uLmNvbS1wcm9kEoADETQD6R0H/h9fyg0Hw7mj0M7T4s0bcBf4fMhARpwk2X4HpvB49bJ5Yvc4t41mAnXGe/wiXbzsddKMiMffkSE1QWK1CFPBgziU23y1PjQToGiIv/sJIFRKRJ4qMBxIl95xlvSEzKdt68n7wqGa442+uAgk7CXU3uTfVofYY76CrPBnEKQfad/CVqTh48geNTb4qRH1TX30NzCsB9NWlcdvg10pCnWSm8cSHu1d9yH+2yQgsGe52QoHHCqHNzG/wAxMYWTevXQW7EPTBeFySPY0xUN+2F2FhCf5/A7uFUHywd0zNTswh0QJc93LBTh46clRLO+d4RKBiBSj3rah6Y5iXMw9N9o58tCRc9gFHrjfMNubopWHjDOO3ATUgqXrTp+fKVCmsGuGl1ComHxXV9i1AqHwzzY2JY2vFqo73jR3IElr6oChPIwcNokmNc0D4TXtjE0BoYkbWKJfHvJJihzMOvDicWUsemVHvua9/FBtpbHgpbgwijFPjtQF9Ldb8Swf"
        # del headers["User-Agent"]
        wv = RemoteDevice(self.host, self.key)
        (session_id, challenge) = wv.get_license_challenge(self.clean_pssh(pssh), cert)
        print('Sending license request')
        res = self.session.post(url=url, params={}, headers=headers, data={'widevine2Challenge': base64.b64encode(challenge).decode('utf-8'), 'includeHdcpTestKeyInLicense': 'true'})
        try:
            data = res.json()
            license_base64 = data['widevine2License']['license']
        finally:
            pass
            

        keys =wv.get_keys(license_base64, session_id)
        return (lambda x: [ f"{k['kid']}:{k['key']}" for k in x ])(keys)


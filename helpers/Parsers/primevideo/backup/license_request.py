import base64
import json
import logging

import requests

from pywidevine.decrypt.wvdecryptcustom import WvDecrypt


class license_request:
    def __init__(self):
        """CLASS FOR AMZN License"""
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()

    def widevine_cert(self, challenge, url, headers):
        r = self.session.post(
            url=url,
            headers=headers,
            data={"widevine2Challenge": base64.b64encode(challenge)},
        )

        try:
            return r.json()["widevine2License"]["license"]
        except Exception:
            self.logger.error("License Acquisition failed!\n{}".format(r.text))
            exit(-1)

        return

    def _license(self, url, headers, pssh=None, cert=False, device=None):
        # cert = None if cert is False else self.widevine_cert(b"\x08\x04", url, headers)
        cert = "CAUSwgUKvAIIAxIQCuQRtZRasVgFt7DIvVtVHBi17OSpBSKOAjCCAQoCggEBAKU2UrYVOSDlcXajWhpEgGhqGraJtFdUPgu6plJGy9ViaRn5mhyXON5PXmw1krQdi0SLxf00FfIgnYFLpDfvNeItGn9rcx0RNPwP39PW7aW0Fbqi6VCaKWlR24kRpd7NQ4woyMXr7xlBWPwPNxK4xmR/6UuvKyYWEkroyeIjWHAqgCjCmpfIpVcPsyrnMuPFGl82MMVnAhTweTKnEPOqJpxQ1bdQvVNCvkba5gjOTbEnJ7aXegwhmCdRQzXjTeEV2dO8oo5YfxW6pRBovzF6wYBMQYpSCJIA24ptAP/2TkneyJuqm4hJNFvtF8fsBgTQQ4TIhnX4bZ9imuhivYLa6HsCAwEAAToPYW1hem9uLmNvbS1wcm9kEoADETQD6R0H/h9fyg0Hw7mj0M7T4s0bcBf4fMhARpwk2X4HpvB49bJ5Yvc4t41mAnXGe/wiXbzsddKMiMffkSE1QWK1CFPBgziU23y1PjQToGiIv/sJIFRKRJ4qMBxIl95xlvSEzKdt68n7wqGa442+uAgk7CXU3uTfVofYY76CrPBnEKQfad/CVqTh48geNTb4qRH1TX30NzCsB9NWlcdvg10pCnWSm8cSHu1d9yH+2yQgsGe52QoHHCqHNzG/wAxMYWTevXQW7EPTBeFySPY0xUN+2F2FhCf5/A7uFUHywd0zNTswh0QJc93LBTh46clRLO+d4RKBiBSj3rah6Y5iXMw9N9o58tCRc9gFHrjfMNubopWHjDOO3ATUgqXrTp+fKVCmsGuGl1ComHxXV9i1AqHwzzY2JY2vFqo73jR3IElr6oChPIwcNokmNc0D4TXtjE0BoYkbWKJfHvJJihzMOvDicWUsemVHvua9/FBtpbHgpbgwijFPjtQF9Ldb8Swf"
        # del headers["User-Agent"]
        headers = {k: v for k, v in headers.items() if k != "User-Agent"}
        wvdecrypt = WvDecrypt(pssh, cert, device)
        challenge = wvdecrypt.get_challenge()
        license_b64 = self.widevine_cert(challenge, url, headers)
        wvdecrypt.update_license(license_b64)
        _, keyswvdecrypt = wvdecrypt.start_process()
        KEYS = keyswvdecrypt
        return KEYS

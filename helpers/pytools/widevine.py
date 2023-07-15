import base64
import logging

# from pywidevine.cdm import cdm, deviceconfig
from pywidevine.decrypt.wvdecryptcustom import WvDecrypt


class widevine:
    def __init__(self,):
        """WIDEVINE DECRYPTION"""
        self.logger = logging.getLogger(__name__)

    def b64encode(self, content):
        try:
            lb64 = base64.b64encode(content)
        except TypeError:
            self.logger.info(
                "Invalid response content: {}".format(content.decode("utf-8"))
            )

        return lb64

    def get_challenge(self, init_data_b64, cert_data_b64, device):
        self.Wv = WvDecrypt(
            init_data_b64=init_data_b64, cert_data_b64=cert_data_b64, device=device,
        )
        self.challenge = self.Wv.get_challenge()

        return self.Wv.get_challenge()

    def update_license(self, license_, encode_license=False):
        if encode_license:
            self.Wv.update_license(self.b64encode(license_))
            return

        self.Wv.update_license(license_)

    def get_keys(self,):
        Correct = False
        while Correct is False:
            Correct, keys = self.Wv.start_process()
        return keys

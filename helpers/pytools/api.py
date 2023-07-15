import base64
import json
import logging

import requests


class api:
    def __init__(self,):
        """WIDEVINE DECRYPTION"""
        self.api_key = ""
        self.url = ""
        self.proxies = ""
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.proxies.update(dict(http=self.proxies, https=self.proxies,))
        self.logger = logging.getLogger(__name__)

    def check_resp(self, response: dict):
        if not response["success"]:
            raise ValueError("Error: {}".format(response["message"]))

    def disneyplus(self, init_data_b64, cert_data_b64, token):
        data = {
            "key": self.api_key,
            "site_name": "disneyplus",
            "site_params": {
                "token": token,
                "init_data_b64": init_data_b64,
                "cert_data_b64": cert_data_b64,
            },
        }

        self.logger.info("\nGETTING KEYS FROM API...")
        response = self.session.post(self.url, data=json.dumps(data)).json()

        self.check_resp(response)

        if not isinstance(response["message"], list) or response["message"] == []:
            raise ValueError("No Keys: {}".format(response["message"]))

        return list(response["message"])

import base64
import binascii
import json
import logging
import os
import subprocess
import uuid
from io import BytesIO

import requests

from pymp4.parser import Box


class pssh(object):
    def __init__(self,):
        self.logger = logging.getLogger(__name__)

    def from_kid(self, kid):
        array_of_bytes = bytearray(b"\x00\x00\x002pssh\x00\x00\x00\x00")
        array_of_bytes.extend(bytes.fromhex("edef8ba979d64acea3c827dcd51d21ed"))
        array_of_bytes.extend(b"\x00\x00\x00\x12\x12\x10")
        array_of_bytes.extend(bytes.fromhex(kid.replace("-", "")))
        pssh = base64.b64encode(bytes.fromhex(array_of_bytes.hex()))
        return pssh.decode()

    def Get_PSSH(self, file, mp4dumpexe=None):
        WV_SYSTEM_ID = "[ed ef 8b a9 79 d6 4a ce a3 c8 27 dc d5 1d 21 ed]"
        pssh = None
        data = subprocess.check_output(
            [mp4dumpexe, "--format", "json", "--verbosity", "1", file]
        )
        data = json.loads(data)
        for atom in data:
            if atom["name"] == "moov":
                for child in atom["children"]:
                    if child["name"] == "pssh":
                        if child["system_id"] == WV_SYSTEM_ID:
                            pssh = child["data"][1:-1].replace(" ", "")
                            pssh = binascii.unhexlify(pssh)
                            if pssh.startswith(b"\x08\x01"):
                                pssh = pssh[0:]
                            pssh = base64.b64encode(pssh).decode("utf-8")
                            return pssh

        if not pssh:
            self.logger.info("Error while generate pssh from file.")
            return pssh

    def get_moov_pssh(self, moov):
        while True:
            x = Box.parse_stream(moov)
            if x.type == b"moov":
                for y in x.children:
                    if y.type == b"pssh" and y.system_ID == uuid.UUID(
                        "edef8ba9-79d6-4ace-a3c8-27dcd51d21ed"
                    ):
                        data = base64.b64encode(y.init_data)
                        return data

    def build(self, BYTES):
        moov = BytesIO(BYTES)
        try:
            data = self.get_moov_pssh(moov)
        except Exception as e:
            self.logger.info("Error while generate pssh: {}".format(e))
            exit(-1)
        pssh = data.decode("utf-8")
        return pssh

    def loads(self, init, headers={}):
        

        if isinstance(init, bytes):
            return self.build(init)

        if isinstance(init, str):
            if init.startswith("http"):
                return self.build(requests.get(init, headers=headers).content)

            try:
                BYTES = open(init, "rb").read()
                return self.build(BYTES)
            except FileNotFoundError:
                pass

        return None

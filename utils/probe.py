import base64
import binascii
import json
import logging
import os
import re
import struct
import subprocess
import uuid
from io import BytesIO
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Union

import requests

log = logging.getLogger(__name__)


def extract_pssh_box(rawpssh: str) -> str:
    try:
        init = base64.b64decode(rawpssh)
        _, = struct.unpack(">I", init[0:4])
        _, = struct.unpack(">I", init[4:8])
        version, = struct.unpack(">I", init[8:12])
        _ = init[12:28]

        position = 28
        kids = []

        if version == 1:
            num_kids, = struct.unpack(">I", init[position:position+4])
            position += 4
            for _ in range(num_kids):
                kids.append(binascii.b2a_hex(init[position:position+16]).decode())
                position += 16

        data_length, = struct.unpack(">I", init[position:position+4])
        position += 4
        b64pssh = base64.b64encode(init[position:position+data_length]).decode()
        return b64pssh
    except Exception:
        return rawpssh


class probe:
    def __init__(self, path: str, mp4dump: str):
        self.path = path
        self.mp4dump = mp4dump
        self.data = self.mp4_dump()
        self.kid = self._kid()
        self.raw_pssh = self._pssh()
        self.pssh = extract_pssh_box(self.raw_pssh)

    def mp4_dump(self) -> Dict[str, Any]:
        stdout = subprocess.check_output(
            [self.mp4dump, "--format", "json", "--verbosity", "1", self.path],
        encoding="utf8")
        return json.loads(stdout)

    def _kid(self) -> Union[str, None]:
        if (kid := re.search(r"'default_KID': '\[(.+?)\]", str(self.data))):
            if len((kid := re.sub(" ", "", kid.group(1)))) != 32:
                kid = "None"
        return kid

    def _pssh(self) -> Union[str, None]:
        pssh = "None"
        for atom in self.data:
            if atom["name"] == "moov":
                for children in atom["children"]:
                    if children["name"] == "pssh" and children["system_id"] == "[ed ef 8b a9 79 d6 4a ce a3 c8 27 dc d5 1d 21 ed]":
                        pssh = re.sub(" ", "", children["data"][1:-1])
                        if (pssh := binascii.unhexlify(pssh)).startswith(b"\x08\x01"): pssh = pssh[0:]
                        pssh = base64.b64encode(pssh).decode("utf-8")
        return pssh

